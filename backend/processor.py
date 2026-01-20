import pandas as pd
import re
import uuid
import json
import os
import math
import copy
import time
import asyncio
from openai import OpenAI
import httpx
from backend.database import get_collection
from backend.llm_client import llm_client
from concurrent.futures import ThreadPoolExecutor
from pymongo import UpdateOne

# Note: We use llm_client for all LLM operations (Azure Claude + Azure OpenAI fallback)
# No direct OpenAI client needed here

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

# Pre-compile regex for speed (re-use across 100k+ rows)
SIZE_REGEX = re.compile(r"(\d+(\.\d+)?)")

def extract_size_val(size_str):
    """Extract numeric size value from string (e.g. '130g' -> 130.0)."""
    if not isinstance(size_str, str):
        return 0.0
    match = SIZE_REGEX.search(size_str)
    if match:
        try:
            return float(match.group(1))
        except:
            return 0.0
    return 0.0

async def process_excel_flow_1(file_contents, request=None):
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
        # Check for disconnection at the start of each sheet
        if request and await request.is_disconnected():
            print(f"Stopping Flow 1: Client disconnected before sheet {sheet_name}")
            return sheets_info

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
        print(f"[{sheet_name}] Starting UPC-based merging for {len(df)} rows...")
        
        # SPEED OPTIMIZATION: Pre-calculate size values once for the entire dataframe
        # This avoids calling regex 180,000+ times inside the groupby loop.
        if size_col:
            df["_size_val"] = df[size_col].astype(str).apply(extract_size_val)
        else:
            df["_size_val"] = 0.0
        
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

        # ULTRA FAST VECTORIZED PROCESSING
        # 1. Sort the entire dataframe by group keys and size
        print(f"[{sheet_name}] Sorting records for vectorized processing...")
        df = df.sort_values(by=group_keys + ["_size_val"]).reset_index(drop=True)

        # 2. Detect Cluster Boundaries (Vectorized)
        # Identify where group keys change
        group_changed = pd.Series(False, index=df.index)
        for key in group_keys:
            group_changed |= (df[key] != df[key].shift(1))
            
        # Identify where size difference > 5.0
        size_diff = df["_size_val"].diff().abs().fillna(0) > 5.0
        
        # New cluster starts if group keys change OR size diff > 5.0
        cluster_start = group_changed | (size_diff & ~group_changed)
        df["_cluster_id"] = cluster_start.cumsum()

        # 3. Mass Aggregation (Vectorized)
        print(f"[{sheet_name}] Performing mass aggregation on {df['_cluster_id'].nunique()} clusters...")
        
        # Define how to aggregate each column
        agg_map = {
            upc_col: 'first',
            "_size_val": 'first', # For metadata
        }
        for col in descriptive_cols:
            if col != upc_col: agg_map[col] = 'first'
        for col in monthly_cols:
            agg_map[col] = 'sum'
            
        # Add special aggregations
        if item_col:
            # Collect list of item names
            agg_map[item_col] = lambda x: list(x)
        
        # Compute everything in one go
        df_merged = df.groupby("_cluster_id").agg(agg_map)
        
        # Add counts
        df_merged["merged_from_docs"] = df.groupby("_cluster_id").size()

        # 4. Final Record Construction (Ultra-Fast Vectorized)
        print(f"[{sheet_name}] Constructing final master records (Vectorized)...")
        
        # Pre-calculate metadata base
        merge_rule_base = "UPC"
        if market_col: merge_rule_base += " + Market"
        if mpack_col: merge_rule_base += " + MPack"
        if facts_col: merge_rule_base += " + Facts"
        
        # Convert the entire aggregated DF to records list at once (Lightning Fast)
        master_records_raw = df_merged.reset_index().to_dict('records')
        single_stock_records = []
        
        # Now we just need to add the Unique/calculated fields
        # Processing in construction chunks to keep is_disconnected check reactive
        const_chunk_size = 1000
        for i in range(0, len(master_records_raw), const_chunk_size):
            if request and await request.is_disconnected():
                print(f"Stopping Flow 1: Client disconnected during record construction")
                return sheets_info
            
            chunk = master_records_raw[i:i + const_chunk_size]
            for row in chunk:
                brand = str(row.get("BRAND", "UNKNOWN"))
                merged_count = int(row["merged_from_docs"])
                
                # Metadata Injection
                row["merge_id"] = f"{brand}_{uuid.uuid4().hex}"
                row["merged_from_docs"] = merged_count
                row["merge_rule"] = merge_rule_base + (" + Size(5g)" if size_col and merged_count > 1 else "")
                row["merged_upcs"] = [str(row[upc_col])]
                row["merge_level"] = "NO_MERGE" if merged_count == 1 else f"MERGED_{merged_count}_VARIANTS"
                row["sheet_name"] = "wersel_match"
                
                # Create merge_items list AND preserve ITEM field for Flow 2
                if item_col:
                    items_list = row.get(item_col, [])
                    # Ensure it's a list
                    if not isinstance(items_list, list):
                        items_list = [items_list]
                    row["merge_items"] = items_list
                    # Preserve ITEM field with first item name for Flow 2 AI processing
                    row["ITEM"] = items_list[0] if items_list else f"UPC_{row[upc_col]}"
                else:
                    row["merge_items"] = [f"UPC_{row[upc_col]}"] * merged_count
                    row["ITEM"] = f"UPC_{row[upc_col]}"
                
                # Cleanup internal agg fields
                row.pop("_cluster_id", None)
                row.pop("_size_val", None)
                
                single_stock_records.append(row)

        # Store in SINGLE_STOCK with ultra-fast insert_many
        single_stock_coll = get_collection("SINGLE_STOCK")
        
        # Delete only records from this sheet_name
        single_stock_coll.delete_many({"sheet_name": "wersel_match"})
        
        if single_stock_records:
            # BATCHED PERSISTENCE: 1000 records per batch for granular progress
            record_chunk_size = 1000
            total_records = len(single_stock_records)
            
            for i in range(0, total_records, record_chunk_size):
                if request and await request.is_disconnected():
                    print(f"Stopping Flow 1: Client disconnected before final DB save")
                    return sheets_info
                
                chunk = single_stock_records[i:i + record_chunk_size]
                if chunk:
                    # use insert_many for maximum speed
                    single_stock_coll.insert_many(chunk, ordered=False)
                    print(f"[{sheet_name}] OK | Saved batch: {min(i + record_chunk_size, total_records)}/{total_records} master records.")
                
                await asyncio.sleep(0)
        
        sheets_info[sheet_name] = {
            "raw_count": len(df),
            "single_stock_count": len(single_stock_records)
        }
        print(f"[{sheet_name}] SUCCESS | {len(single_stock_records)} master records created from {len(df)} raw rows.")
    
    print(f"Flow 1 Processing Completed for all sheets.")
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
5. PRESERVE THE WORDS "BRAND" AND "FLAVOUR" if they appear in the input description; they are required for comparison.
6. Output STRICT JSON only.

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
    # 1. ITEM Management
    current_item = base.get("ITEM", "")
    
    # 2. Raw Items Collection (from merge_items list of SINGLE_STOCK docs)
    raw_source_items = []
    for d in group_docs:
        mi = d.get("merge_items")
        if isinstance(mi, list):
            raw_source_items.extend(mi)
        elif mi:
            raw_source_items.append(str(mi))
        elif d.get("ITEM"):
            raw_source_items.append(d.get("ITEM"))
            
    # Unique and Filter current_item to avoid redundancy
    unique_raw = sorted(list(dict.fromkeys([str(x) for x in raw_source_items if x])))
    if current_item in unique_raw: 
        unique_raw.remove(current_item)
    
    # 3. Construct Piped String: Clean | Raw1 | Raw2
    if current_item:
        base["merge_items"] = " | ".join([current_item] + unique_raw)
    else:
        base["merge_items"] = " | ".join(unique_raw)

    # 4. Other Metadata
    base["merged_upcs"] = list(dict.fromkeys(
        base.get("merged_upcs", []) +
        [str(d.get("UPC")) for d in group_docs if d.get("UPC")]
    ))
    
    base["merged_from_docs"] = base.get("merged_from_docs", 0) + len(group_docs)
    
    prev_rule = base.get("merge_rule")
    base["merge_rule"] = (
        prev_rule + " | " + merge_rule if prev_rule else merge_rule
    )
    
    # Standardize merge_level as a list/string per user example
    new_levels = []
    prev_level = base.get("merge_level")
    if prev_level:
        if isinstance(prev_level, list): new_levels = prev_level
        else: new_levels = [prev_level]
    
    if merge_level not in new_levels:
        new_levels.append(merge_level)
    
    base["merge_level"] = new_levels


def simple_clean_item(name):
    """Fallback cleaner for when AI fails. Extracts and sorts unique keywords."""
    if not name: return ""
    s = str(name).upper()
    # Remove noise (Keep BRAND and FLAVOUR as per client requirement for comparison)
    noise = ["FLV", "PRODUCT", "PACK", "ITEM", "X1", "POCKY", "GLICO", "OREO"]
    # Standardize spaces
    for word in noise:
        s = s.replace(word, " ")
    
    # Take alphanumeric words only and sort them
    words = sorted(list(set(re.findall(r'[A-Z0-9]+', s))))
    return " ".join(words).strip()


async def process_llm_mastering_flow_2(sheet_name, request=None):

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

    def get_doc_item(d):
        # Prefer 'ITEM' if exists, else take first from 'merge_items' list
        if d.get("ITEM"): return d.get("ITEM")
        mi = d.get("merge_items")
        if mi and isinstance(mi, list) and len(mi) > 0: return mi[0]
        # Fallback to other descriptive fields
        return d.get("BRAND", "") + " " + d.get("VARIANT", "")

    unique_items = list(set([get_doc_item(d) for d in docs if get_doc_item(d)]))
    
    norm_map = {}
    
    # Process in batches to avoid rate limits
    batch_size = 50
    total_batches = (len(unique_items) + batch_size - 1) // batch_size
    
    print(f"Processing {len(unique_items)} unique items in {total_batches} batches...")
    
    for batch_num in range(total_batches):
        # Check for disconnection before starting a new batch of LLM calls
        if request and await request.is_disconnected():
            print(f"Stopping Flow 2: Client disconnected before batch {batch_num + 1}")
            return {"status": "Stopped | Client disconnected"}

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
        item = get_doc_item(d)
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
        fact_val = get_val(d, ["FACTS", "FACT"])
        
        if norm.get("confidence", 0) >= LLM_CONFIDENCE_THRESHOLD:
            # HIGH CONFIDENCE: Group by AI-standardized attributes + Exact Fact
            # (Keeping exact Fact name ensures we have 6 rows per product if there are 6 facts)
            pre_group_key = (
                f"{norm.get('brand')}|{norm.get('flavour')}|"
                f"{market_val}|{mpack_val}|{fact_val}"
            )
        else:
            # LOW CONFIDENCE: Fallback to Cleaned keywords + Exact Fact
            clean_item = simple_clean_item(item)
            pre_group_key = (
                f"LOW_CONF|{clean_item}|"
                f"{market_val}|{mpack_val}|{fact_val}"
            )
        
        pre_groups.setdefault(pre_group_key, []).append(d)


    # Apply Size Tolerance (5g Rules) within each Brand+Flavour+Market bucket
    final_groups_list = []
    
    for pg_key, pg_docs in pre_groups.items():
        # Add numeric size for tolerance check
        for d in pg_docs:
            # item is used to look up norm - use helper function
            norm = norm_map.get(get_doc_item(d), {})
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
    print(f"Final Phase: Saving master stock clusters to database...")

    # Process Groups
    cluster_count = 0
    for group_docs in final_groups_list:
        cluster_count += 1
        if cluster_count % 100 == 0:
             print(f"Flow 2: Cluster processing progress: {cluster_count}/{len(final_groups_list)}")

    
    # Process Groups
    for group_docs in final_groups_list:
        # Check for disconnection during final cluster processing
        if request and await request.is_disconnected():
            print(f"Stopping Flow 2: Client disconnected during final cluster processing")
            return {"status": "Stopped | Client disconnected"}

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
            
            # Get norm from the first item using helper function
            item_name = get_doc_item(group_docs[0])
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
        
        # Get norm from first item using helper function
        item_name = get_doc_item(group_docs[0])
        norm = norm_map.get(item_name, {})
        
        base["brand"] = norm.get("brand") or base.get("BRAND", "")
        base["flavour"] = norm.get("flavour") or base.get("VARIANT", "") or ""
        base["size"] = norm.get("size") or base.get("NRMSIZE", "")
        base["normalized_item"] = norm.get("base_item") or base.get("ITEM", "")
        base["llm_confidence_min"] = min([norm_map.get(get_doc_item(d), {}).get("confidence", 0) for d in group_docs])

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
        
        # Prepare operational batching
        if not hasattr(process_llm_mastering_flow_2, "_batch_ops"):
            process_llm_mastering_flow_2._batch_ops = []
        
        process_llm_mastering_flow_2._batch_ops.append(
            UpdateOne(
                {"merge_id": base["merge_id"], "sheet_name": base["sheet_name"]},
                {"$set": base},
                upsert=True
            )
        )
        
        # Write in batches of 100 during grouping (Flow 2 is slower due to AI counts anyway)
        if len(process_llm_mastering_flow_2._batch_ops) >= 100:
            tgt_col.bulk_write(process_llm_mastering_flow_2._batch_ops)
            process_llm_mastering_flow_2._batch_ops = []
            await asyncio.sleep(0) # Yield for disconnect checks
            
        print(f"PROCESSED CLUSTER | {base['BRAND']} | items={len(base['merge_items'])}")
    
    # Final flush for Flow 2
    if hasattr(process_llm_mastering_flow_2, "_batch_ops") and process_llm_mastering_flow_2._batch_ops:
        tgt_col.bulk_write(process_llm_mastering_flow_2._batch_ops)
        process_llm_mastering_flow_2._batch_ops = []
    
    print(f"Flow 2 AI Mastering Completed: {len(final_groups_list)} master clusters saved.")

    
    return {
        "total_processed": len(docs),
        "clusters_created": len(final_groups_list),
        "status": "Success | All items processed and merged according to client rules."
    }

