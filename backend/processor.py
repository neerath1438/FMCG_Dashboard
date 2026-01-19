import pandas as pd
import re
import uuid
import json
import os
import math
import copy
import time
from openai import OpenAI
import httpx
from backend.database import get_collection
from backend.llm_client import llm_client
from concurrent.futures import ThreadPoolExecutor
from pymongo import UpdateOne

# Initialize OpenAI client (Docker-compatible)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx.Client()
)

# Configuration
LLM_CONFIDENCE_THRESHOLD = 0.80
OPENAI_MODEL = "gpt-4o"


# LLM cache to avoid duplicate API calls
llm_cache = {}

def get_cached_llm_result(item):
    """Fetch result from MongoDB cache."""
    cache_coll = get_collection("LLM_CACHE_STORAGE")
    return cache_coll.find_one({"item": item}, {"_id": 0})

def save_to_llm_cache(item, result):
    """Save result to MongoDB cache."""
    cache_coll = get_collection("LLM_CACHE_STORAGE")
    cache_coll.update_one(
        {"item": item},
        {"$set": {"item": item, "result": result}},
        upsert=True
    )

def extract_size_val(size_str):
    """Extract numeric size value from string (e.g. '130g' -> 130.0)."""
    if not isinstance(size_str, str):
        return 0.0
    match = re.search(r"(\d+(\.\d+)?)", size_str)
    if match:
        try:
            return float(match.group(1))
        except:
            return 0.0
    return 0.0

def process_excel_flow_1(file_contents):
    """
    Flow 1: Strict UPC + Attribute merging with Size Tolerance.
    Supports Excel (.xlsx, .xls) and CSV (.csv) files.
    Groups by UPC, Markets, MPACK, Facts to separate variants/metrics.
    Merges sizes within 5g tolerance inside each group.
    """
    import io
    
    # Detect file type and read accordingly
    try:
        # Try reading as Excel first
        xl = pd.ExcelFile(file_contents)
        is_excel = True
        sheet_names = xl.sheet_names
    except:
        # If Excel fails, treat as CSV
        is_excel = False
        # Reset file pointer
        if hasattr(file_contents, 'seek'):
            file_contents.seek(0)
        # Read CSV
        df_csv = pd.read_csv(file_contents)
        sheet_names = ['CSV_Data']  # Single sheet for CSV
    
    sheets_info = {}
    
    for sheet_name in sheet_names:
        # Get DataFrame based on file type
        if is_excel:
            df = xl.parse(sheet_name)
        else:
            df = df_csv  # Use the CSV data
        
        # KEY COLUMN IDENTIFICATION
        # Normalize columns slightly for matching but keep original for access
        col_map = {c.upper().strip(): c for c in df.columns}
        
        # Must have UPC
        if "UPC" not in col_map:
            continue
            
        upc_col = col_map["UPC"]
        
        # Optional strict grouping keys
        market_col = col_map.get("MARKETS")
        mpack_col = col_map.get("MPACK")
        facts_col = col_map.get("FACTS")
        
        # Size for tolerance
        size_col = col_map.get("NRMSIZE")
        
        # Product Name
        item_col = col_map.get("ITEM") or col_map.get("PRODUCT NAME") or col_map.get("DESCRIPTION")
        
        # Store raw data - Preserve all rows
        raw_coll = get_collection(f"{sheet_name}_RAW")
        raw_coll.delete_many({"sheet_name": "welrsel_match"})
        
        rows_to_insert = []
        # Convert NaNs to None/empty for JSON safety before raw insert
        df_raw = df.replace({pd.NA: None, float('nan'): None})
        for row in df_raw.to_dict("records"):
            row["sheet_name"] = "welrsel_match"
            rows_to_insert.append(row)
            
        if rows_to_insert:
            raw_coll.insert_many(rows_to_insert)
        
        # Identify monthly/metric columns
        # Exclude specific non-monthly columns that might accidentally match (e.g. "Markets" matches "MAR")
        PROTECTED_COLS = ["MARKETS", "MARKET", "MPACK", "PACK", "BRAND", "ITEM", "UPC", "FACTS", "FACT", "NRMSIZE", "SIZE"]
        
        monthly_cols = [c for c in df.columns if 
            any(m in str(c).upper() for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "W/E", "MAT"])
            and str(c).upper().strip() not in PROTECTED_COLS
        ]
        
        # Columns to keep value from first item (descriptive)
        ignore_cols = monthly_cols + [upc_col]
        if facts_col: ignore_cols.append(facts_col) # Facts is grouping key, but we handle it
        
        descriptive_cols = [c for c in df.columns if c not in ignore_cols]
        
        # Filter valid UPCs
        df = df[df[upc_col].notnull()].copy()
        
        # PREPARE FOR GROUPING
        # Fill NaNs for grouping keys to avoid exclusion
        fill_val = "UNKNOWN"
        group_keys = [upc_col]
        
        if market_col: 
            df[market_col] = df[market_col].fillna(fill_val)
            group_keys.append(market_col)
        if mpack_col: 
            df[mpack_col] = df[mpack_col].fillna(fill_val)
            group_keys.append(mpack_col)
        if facts_col: 
            df[facts_col] = df[facts_col].fillna(fill_val)
            group_keys.append(facts_col)

        # Process Groups
        single_stock_records = []
        
        for group_ids, group in df.groupby(group_keys):
            # Parse sizes for tolerance handling
            group = group.copy()
            if size_col:
                group["_size_val"] = group[size_col].astype(str).apply(extract_size_val)
                # Sort by size to make bucketing easier
                group = group.sort_values("_size_val")
            else:
                group["_size_val"] = 0.0
            
            # Bucketing Logic (5g tolerance)
            buckets = []
            current_bucket = []
            
            for _, row in group.iterrows():
                if not current_bucket:
                    current_bucket.append(row)
                    continue
                
                prev_row = current_bucket[-1]
                diff = abs(row["_size_val"] - prev_row["_size_val"])
                
                if diff <= 5.0:
                    current_bucket.append(row)
                else:
                    buckets.append(current_bucket)
                    current_bucket = [row]
            
            if current_bucket:
                buckets.append(current_bucket)
            
            # Process each bucket (Create ONE record per bucket)
            for bucket in buckets:
                base_row = bucket[0]
                merged_count = len(bucket)
                
                # Get all item names in this bucket
                product_names = []
                if item_col:
                    product_names = [r[item_col] for r in bucket]
                else:
                    product_names = [f"UPC_{base_row[upc_col]}"] * merged_count
                
                # Base Record
                merged_record = {"UPC": base_row[upc_col]}
                
                # Add Grouping Keys explicitly
                if market_col: merged_record[market_col] = base_row[market_col]
                if mpack_col: merged_record[mpack_col] = base_row[mpack_col]
                if facts_col: merged_record[facts_col] = base_row[facts_col]
                
                # Add Descriptive Columns (Take from first)
                for col in descriptive_cols:
                    if col in base_row and col not in merged_record:
                        merged_record[col] = base_row[col]
                
                # Sum Monthly Columns
                for col in monthly_cols:
                    total = 0.0
                    if col in base_row: # Check existence in series
                        for r in bucket:
                            val = r.get(col, 0)
                            try:
                                f_val = float(val)
                                if not math.isnan(f_val):
                                    total += f_val
                            except (ValueError, TypeError):
                                pass
                    merged_record[col] = total
                
                # Metadata
                brand = merged_record.get("BRAND", "UNKNOWN")
                merge_id = f"{brand}_{uuid.uuid4().hex}"
                
                merge_rule_parts = ["UPC"]
                if market_col: merge_rule_parts.append("Market")
                if mpack_col: merge_rule_parts.append("MPack")
                if facts_col: merge_rule_parts.append("Facts")
                if size_col and merged_count > 1: merge_rule_parts.append("Size(5g)")
                
                merged_record["merge_id"] = merge_id
                merged_record["merge_items"] = product_names
                merged_record["merged_from_docs"] = merged_count
                merged_record["merge_rule"] = " + ".join(merge_rule_parts)
                merged_record["merged_upcs"] = [str(base_row[upc_col])]
                
                if merged_count == 1:
                    merged_record["merge_level"] = "NO_MERGE"
                else:
                    merged_record["merge_level"] = f"MERGED_{merged_count}_VARIANTS"
                
                # Add sheet_name for upsert tracking
                merged_record["sheet_name"] = "wersel_match"
                
                single_stock_records.append(merged_record)
        
        # Store in SINGLE_STOCK with upsert logic
        single_stock_coll = get_collection("SINGLE_STOCK")
        
        # Delete only records from this sheet_name
        single_stock_coll.delete_many({"sheet_name": "wersel_match"})
        
        if single_stock_records:
            # Use bulk upsert to prevent duplicates
            operations = []
            for record in single_stock_records:
                # Upsert based on merge_id + sheet_name
                operations.append(UpdateOne(
                    {
                        "merge_id": record["merge_id"],
                        "sheet_name": record["sheet_name"]
                    },
                    {"$set": record},
                    upsert=True
                ))
            
            if operations:
                single_stock_coll.bulk_write(operations)
        
        sheets_info[sheet_name] = {
            "raw_count": len(df),
            "single_stock_count": len(single_stock_records)
        }
    
    return sheets_info


def normalize_item_llm(item):
    """
    Use LLM to extract brand, flavour, size and remove marketing keywords.
    With persistent caching.
    """
    # 1. Check in-memory cache
    if item in llm_cache:
        return llm_cache[item]
    
    # 2. Check persistent MongoDB cache
    cached = get_cached_llm_result(item)
    if cached:
        llm_cache[item] = cached["result"]
        return cached["result"]
    
    system_prompt = """
You are an FMCG product mastering expert specializing in the Malaysian market.

Your task is to extract standardized attributes from raw product descriptions often found in 7-Eleven or POS terminals.

### Standardized Mapping Table:
Use these standardized terms for any raw keywords found:

- PROTEINS:
  - {AYM, CHK, CKN, AYAM} -> CHICKEN
  - {DGG, BF, DAGING} -> BEEF
  - {TLR, EG, TELUR} -> EGG
  - {STNG, SQD, SOTONG} -> SQUID
  - {UDG, UDANG, PRN} -> PRAWN
  - {BILIS, ANC} -> ANCHOVY

- FLAVORS & VARIANTS:
  - {COK, CHOC, CHOCO, COKLAT, CHOKLAT, CHOKIT, COKLIT} -> CHOCOLATE
  - {BAN, BNNA, BANANA} -> BANANA
  - {VAN, VNL, VENLLA, VANILLA} -> VANILLA
  - {PDS, HOT, SPY, PEDAS} -> SPICY
  - {KRI, CRY, KARI} -> CURRY
  - {SSU, MLK, SUSU} -> MILK
  - {KOP, CF, KOPI} -> COFFEE
  - {HLA, GGR, HALIA} -> GINGER
  - {GUL, SGR, GULA} -> SUGAR
  - {STRW, STRAW, STRAWBERRY} -> STRAWBERRY
  - {ORG, ORNG, ORANGE} -> ORANGE
  - {APP, APPL, APPLE} -> APPLE
  - {MNG, MANGO} -> MANGO
  - {PINE, PNAP, PINEAPPLE} -> PINEAPPLE
  - {ORI, ORIG, ORIGINAL} -> ORIGINAL
  - {BLK, BLACK} -> BLACK
  - {WHT, WHITE} -> WHITE
  - {GRN, GREEN} -> GREEN
  - {RD, RED} -> RED
  - {RYAL, ROYAL} -> ROYAL
  - {DBL, DOUBLE, DB} -> DOUBLE
  - {TRP, TRIPLE} -> TRIPLE

- UOM (Volume/Weight):
  - {320M, 320ML} -> 320ML
  - {1.5L, 1.5LTR, 1500M} -> 1500ML
  - {1KG, 1000G} -> 1000G
  - {59GR, 59G} -> 59G
  - {PC, PCS, UNIT} -> UNIT

- BRANDS:
  - {F&N} -> FRASER AND NEAVE
  - {MGG} -> MAGGI
  - {NES} -> NESCAFE
  - {D.LADY, DL} -> DUTCH LADY
  - {YEO, YS} -> YEOS

- PACKAGING:
  - {CAN, CN} -> CAN
  - {BTL, BT} -> BOTTLE
  - {VP, V.PACK} -> MULTIPACK
  - {RTE} -> READY TO EAT

### Few-Shot Examples for Accuracy:
1. Input: "OREO VNL 133G"
   Output: {"brand": "OREO", "flavour": "VANILLA", "size": "133G", "base_item": "OREO VANILLA 133G", "confidence": 1.0}
2. Input: "ARNOTT'S NYAM NYAM RICE CRISPY 22 GM"
   Output: {"brand": "ARNOTTS", "flavour": "RICE CRISPY", "size": "22G", "base_item": "ARNOTTS NYAM NYAM RICE CRISPY 22G", "confidence": 1.0}
3. Input: "GLICO CHOCO BANANA 25GM"
   Output: {"brand": "GLICO", "flavour": "CHOCOLATE BANANA", "size": "25G", "base_item": "GLICO POCKY CHOCOLATE BANANA 25G", "confidence": 1.0}

Rules:
1. Identify BRAND, FLAVOUR, SIZE using the mapping table above.
2. Remove marketing / promo / campaign words (PROMO, PRM, NP, FOC, NEW, OFFER, LIMITED, BEST VALUE, etc.).
3. If a term is not in the table, try to find its English equivalent or keep it as is if it's a specific product name.
4. Do NOT merge different flavours or sizes unless they are logically identical after standardization.
5. Output STRICT JSON only.

"""
    
    user_prompt = f"""
ITEM DESCRIPTION: "{item}"

Return JSON only:
{{
  "brand": "Standardized Brand Name",
  "flavour": "Standardized Flavour Name",
  "size": "Standardized Size (e.g., 320ML, 500G)",
  "base_item": "Standardized Generic Name",
  "removed_marketing_terms": ["list", "of", "removed", "terms"],
  "confidence": 0.0 to 1.0
}}
"""
    
    try:
        raw_content = llm_client.chat_completion(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0
        )
        
        raw_content = raw_content.strip()
        
        # Handle empty response
        if not raw_content or raw_content == '{}':
            print(f"Empty LLM response for '{item}' - using fallback")
            raise ValueError("Empty response from LLM")
        
        # Clean markdown code blocks if present
        if raw_content.startswith("```"):
            # Find first opening brace
            start_idx = raw_content.find("{")
            end_idx = raw_content.rfind("}")
            if start_idx != -1 and end_idx != -1:
                raw_content = raw_content[start_idx:end_idx+1]
        
        data = json.loads(raw_content)
        
        # Validate required fields
        if not data.get("brand") and not data.get("flavour"):
            print(f"Invalid LLM data for '{item}' - missing brand/flavour")
            raise ValueError("Missing required fields")
            
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error for '{item}': {e}")
        print(f"RAW RESPONSE: {raw_content[:200] if raw_content else 'EMPTY'}")
        # Fallback to default
        data = {
            "brand": "",
            "flavour": "",
            "size": "",
            "base_item": item,
            "removed_marketing_terms": [],
            "confidence": 0.0
        }
    except Exception as e:
        print(f"LLM Error for '{item}': {e}")
        # Fallback to default
        data = {
            "brand": "",
            "flavour": "",
            "size": "",
            "base_item": item,
            "removed_marketing_terms": [],
            "confidence": 0.0
        }
    
    # 3. Save to both caches only if we got a valid result
    if data.get("confidence", 0) > 0:
        llm_cache[item] = data
        save_to_llm_cache(item, data)
    return data



def extend_merge_metadata(base, group_docs, merge_rule, merge_level):
    """
    Extend merge metadata for grouped documents.
    """
    base["merge_items"] = list(dict.fromkeys(
        base.get("merge_items", []) +
        [d.get("ITEM") for d in group_docs if d.get("ITEM")]
    ))
    
    base["merged_upcs"] = list(dict.fromkeys(
        base.get("merged_upcs", []) +
        [d.get("UPC") for d in group_docs if d.get("UPC")]
    ))

    
    base["merged_from_docs"] = base.get("merged_from_docs", 0) + len(group_docs)
    
    prev_rule = base.get("merge_rule")
    base["merge_rule"] = (
        prev_rule + " | " + merge_rule if prev_rule else merge_rule
    )
    
    prev_level = base.get("merge_level")
    if prev_level:
        if isinstance(prev_level, list):
            base["merge_level"] = prev_level + [merge_level]
        else:
            base["merge_level"] = [prev_level, merge_level]
    else:
        base["merge_level"] = merge_level


def simple_clean_item(name):
    """Fallback cleaner for when AI fails. Extracts and sorts unique keywords."""
    if not name: return ""
    s = str(name).upper()
    # Remove noise
    for word in ["BRAND", "FLAVOUR", "FLV", "PRODUCT", "PACK", "ITEM", "X1", "POCKY", "GLICO", "OREO"]:
        s = s.replace(word, " ")
    # Take alphanumeric words only and sort them
    words = sorted(list(set(re.findall(r'[A-Z0-9]+', s))))
    return "".join(words)


def process_llm_mastering_flow_2(sheet_name):

    """
    Flow 2: LLM-based mastering.
    Reads from SINGLE_STOCK, creates MASTER_STOCK with LLM-extracted attributes.
    """
    src_col = get_collection("SINGLE_STOCK")
    tgt_col = get_collection("MASTER_STOCK")
    
    # Clear previous master data for this sheet only
    tgt_col.delete_many({"sheet_name": "wersel_match"})
    
    # Only process records from this sheet_name
    docs = list(src_col.find({"sheet_name": "wersel_match"}))
    print(f"Loaded {len(docs)} docs from SINGLE_STOCK for sheet: wersel_match")

    
    groups = {}
    single_docs = []
    
    # 1. Discovery Phase: Extract unique items and fetch attributes in parallel
    print(f"Discovery Phase: Extracting unique attributes for {len(docs)} items...")

    unique_items = list(set([d.get("ITEM") for d in docs if d.get("ITEM")]))
    
    norm_map = {}
    
    # Process in batches to avoid rate limits
    batch_size = 50
    total_batches = (len(unique_items) + batch_size - 1) // batch_size
    
    print(f"Processing {len(unique_items)} unique items in {total_batches} batches...")
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(unique_items))
        batch_items = unique_items[start_idx:end_idx]
        
        print(f"Batch {batch_num + 1}/{total_batches}: Processing {len(batch_items)} items...")
        
        with ThreadPoolExecutor(max_workers=5) as executor:  # Reduced from 10 to 5
            results = list(executor.map(normalize_item_llm, batch_items))
            for item, res in zip(batch_items, results):
                norm_map[item] = res
        
        # Wait between batches to avoid rate limits
        if batch_num < total_batches - 1:
            print(f"Waiting 10 seconds before next batch...")
            time.sleep(10)

            
    # 2. Grouping Phase: Consistently group docs based on extracted attributes + Strict Keys
    print(f"Grouping Phase: Merging items into clusters...")

    
    # Pre-group by everything EXCEPT size to handle size tolerance per Brand+Flavour+Market combo
    pre_groups = {}
    for d in docs:
        item = d.get("ITEM")
        brand = d.get("BRAND")
        if not item: continue
        
        # Get LLM result or use a very basic fallback
        norm = norm_map.get(item, {"brand": brand or "Unknown", "flavour": "Unknown", "size": "Unknown", "confidence": 0})
        
        def get_val(doc, key_list):
            for k, v in doc.items():
                if k.upper() in [x.upper() for x in key_list]: return str(v).strip()
            return "UNKNOWN"
            
        market_val = get_val(d, ["MARKETS", "MARKET"])
        mpack_val = get_val(d, ["MPACK", "PACK"])
        facts_val = get_val(d, ["FACTS", "FACT"])
        
        if norm.get("confidence", 0) >= LLM_CONFIDENCE_THRESHOLD:
            # HIGH CONFIDENCE: Group by AI-standardized attributes + Facts
            pre_group_key = (
                f"{norm.get('brand')}|{norm.get('flavour')}|"
                f"{market_val}|{mpack_val}|{facts_val}"
            )
        else:
            # LOW CONFIDENCE: Fallback to Cleaned keywords + Facts
            clean_item = simple_clean_item(item)
            pre_group_key = (
                f"LOW_CONF|{clean_item}|"
                f"{market_val}|{mpack_val}|{facts_val}"
            )


            
        pre_groups.setdefault(pre_group_key, []).append(d)


    # Apply Size Tolerance (5g Rules) within each Brand+Flavour+Market bucket
    final_groups_list = []
    
    for pg_key, pg_docs in pre_groups.items():
        # Add numeric size for tolerance check
        for d in pg_docs:
            # item is used to look up norm
            norm = norm_map.get(d.get("ITEM"), {})
            d["_size_val"] = extract_size_val(norm.get("size", ""))
            
        # Sort by size
        pg_docs.sort(key=lambda x: x["_size_val"])
        
        # Bucketing
        current_bucket = []
        for d in pg_docs:
            if not current_bucket:
                current_bucket.append(d)
                continue
            
            prev_d = current_bucket[-1]
            if abs(d["_size_val"] - prev_d["_size_val"]) <= 5.0:
                current_bucket.append(d)
            else:
                final_groups_list.append(current_bucket)
                current_bucket = [d]
        if current_bucket:
            final_groups_list.append(current_bucket)

    print(f"Clusters formed after size tolerance: {len(final_groups_list)}")

    
    # Process Groups
    for group_docs in final_groups_list:
        # Sort group docs by 'Facts' priority: prefer 'Sales Value' as the descriptive base
        def facts_priority(doc):
            f = str(doc.get("Facts", doc.get("FACTS", ""))).upper()
            if "VALUE" in f: return 0
            if "UNIT" in f: return 1
            return 2
        
        group_docs.sort(key=facts_priority)

        
        # Single item - no merge
        if len(group_docs) == 1:
            doc = copy.deepcopy(group_docs[0])
            doc.pop("_id", None)
            doc.pop("_norm", None)
            
            # Get norm from the first item
            item_name = group_docs[0].get("ITEM")
            norm = norm_map.get(item_name, {})
            
            doc["brand"] = norm.get("brand")
            doc["flavour"] = norm.get("flavour")
            doc["size"] = norm.get("size")
            doc["normalized_item"] = norm.get("base_item")

            extend_merge_metadata(
                base=doc,
                group_docs=[doc],
                merge_rule="NO MERGE | SINGLE ITEM",
                merge_level="NO_MERGE_SINGLE_ITEM"
            )

            doc["merge_id"] = doc.get("merge_id") or f"{doc['BRAND']}_{uuid.uuid4().hex}"
            
            # Add sheet_name for tracking
            doc["sheet_name"] = "wersel_match"

            
            # Clean up internal fields
            for k in list(doc.keys()):
                if k.startswith("_") or k.lower().startswith("unnamed"):
                    doc.pop(k)
            
            # Upsert instead of insert
            tgt_col.update_one(
                {"merge_id": doc["merge_id"], "sheet_name": doc["sheet_name"]},
                {"$set": doc},
                upsert=True
            )
            print(f"UPSERT AS-IS | {doc['ITEM']}")
            continue

        
        # Merge multiple items
        base = copy.deepcopy(group_docs[0])
        base.pop("_id", None)
        base.pop("_norm", None)
        
        # Sum monthly columns
        month_cols = [k for k in base if "w/e" in k.lower() or "mat" in k.lower()]
        for m in month_cols:
            base[m] = 0.0
        
        for d in group_docs:
            for m in month_cols:
                val = d.get(m)
                # Robust conversion to float
                try:
                    f_val = float(val)
                    if not math.isnan(f_val):
                        base[m] += f_val
                except (ValueError, TypeError):
                    pass
        
        base["merge_id"] = base.get("merge_id") or f"{base['BRAND']}_{uuid.uuid4().hex}"
        
        # Get norm from first item
        item_name = group_docs[0].get("ITEM")
        norm = norm_map.get(item_name, {})
        
        base["brand"] = norm.get("brand") or base.get("BRAND", "")
        base["flavour"] = norm.get("flavour") or base.get("VARIANT", "") or ""
        base["size"] = norm.get("size") or base.get("NRMSIZE", "")
        base["normalized_item"] = norm.get("base_item") or base.get("ITEM", "")
        base["llm_confidence_min"] = min(norm_map.get(d.get("ITEM"), {}).get("confidence", 0) for d in group_docs)


        
        extend_merge_metadata(
            base=base,
            group_docs=group_docs,
            merge_rule="BRAND+FLAVOUR+SIZE (LLM) + STRICT KEYS",
            merge_level="MASTER_PRODUCT_MERGE"
        )

        
        # Add sheet_name for tracking
        base["sheet_name"] = "wersel_match"
        
        # Clean up
        for k in list(base.keys()):
            if k.startswith("_") or k.lower().startswith("unnamed"):
                base.pop(k)
        
        # Upsert instead of insert
        tgt_col.update_one(
            {"merge_id": base["merge_id"], "sheet_name": base["sheet_name"]},
            {"$set": base},
            upsert=True
        )
        print(f"UPSERT MERGED | {base['BRAND']} | items={len(base['merge_items'])}")

    
    return {
        "total_processed": len(docs),
        "clusters_created": len(final_groups_list),
        "status": "Success | All items processed and merged according to client rules."
    }

