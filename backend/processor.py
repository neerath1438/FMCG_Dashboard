import pandas as pd
import numpy as np  # For vectorized bucketing
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
from backend.database import get_collection, reset_main_collections, RAW_DATA_COL, SINGLE_STOCK_COL, MASTER_STOCK_COL
from backend.llm_client import llm_client, flow2_client  # Import both clients
from concurrent.futures import ThreadPoolExecutor
from pymongo import UpdateOne
from difflib import SequenceMatcher

# Note: We use llm_client for all LLM operations (Azure Claude + Azure OpenAI fallback)
# No direct OpenAI client needed here

# Configuration
LLM_CONFIDENCE_THRESHOLD = 0.92  # Raised from 0.80 for production-grade safety
OPENAI_MODEL = "gpt-4o-mini"


# LLM cache to avoid duplicate API calls
llm_cache = {}

def normalize_mpack(mpack_str: str) -> str:
    """Normalize X1, 1, 1X, 1S into X1. Ignores high piece counts like 32P."""
    if not mpack_str: return "X1"
    s = str(mpack_str).upper().replace(" ", "").replace("(", "").replace(")", "")
    
    # Ignore piece counts like 32P, 14PCS if they are likely internal pieces
    if re.search(r'(\d+)(P|PCS)$', s):
        val = int(re.search(r'(\d+)', s).group(1))
        if val > 10: # If more than 10 pieces, it's likely internal, not a multipack
            return "X1"

    # Remove 'S' if it follows a number (e.g., 6S -> 6)
    s = re.sub(r'(\d+)S$', r'\1', s)
    # Extract digit
    match = re.search(r'(\d+)', s)
    if match:
        return f"X{match.group(1)}"
    return "X1"

def normalize_synonyms(item_name: str) -> str:
    """Normalize common FMCG synonyms to improve fuzzy matching."""
    if not item_name: return ""
    s = str(item_name).upper()
    # ✅ Add space between letters and numbers (e.g., OAT600G -> OAT 600G)
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    # ✅ Removed apostrophes and backticks for consistent matching (e.g. O'SOY -> OSOY)
    s = s.replace("'", "").replace("`", "")
    # ✅ Remove Piece Counts (e.g., 9PCS, 10 PCS) - they often vary between same items
    s = re.sub(r'\b\d+\s*PCS\b', ' ', s)
    # ✅ Separate multipliers safely (e.g., 428GMX12 -> 428 GM X 12)
    # Only split if X is near a digit to avoid splitting words like LEXUS
    s = re.sub(r'(\d)([X\*])', r'\1 \2', s)
    s = re.sub(r'([X\*])(\d)', r'\1 \2', s)
    # Handle GMX12 case specifically without splitting LEXUS
    s = re.sub(r'([A-Z]{2,})([X\*])(\d+)', r'\1 \2 \3', s)
    
    # Define synonym maps
    syns = {
        "CHOCOLATE": ["COCOA", "CHOC", "CHOCO", "COK", "CHCO"],
        "STRAWBERRY": ["S/BERRY", "SBERRY", "STRWB", "STRW", "S/BERY"],
        "VANILLA": ["VAN", "VNL", "VNLA"],
        "PEANUT": ["PNUT", "PNT", "P-NUT"],
        "NEAPOLITAN": ["NPLTNE", "NAPOLITANER"],
        "ASSORTED": ["ASST", "ASSTD", "MIX"],
        "CHOCOLATE CHIP": ["C/CHIP", "CHOC CHIP", "CHIP", "CHOC CHIPS"],
        "SALTED CARAMEL": ["SALTED CRMEL", "SALT CRMEL", "SALTED CARAMEL"],
        "MACADAMIA": ["MCDAMIA", "MACDAMIA", "MACADMIA"],
        "CRANBERRY": ["CRNBER", "CRNBERRIES", "CRNBERY", "CRNBRIES"],
        "BLACKCURRANT": ["B/CURR", "BCURR", "BLACKCURR"],
        "HAZELNUT": ["HZLNT", "HZLNUT", "H/NUT"],
        "PISTACHIO": ["PSTCHIO", "PISTCH"],
        "GRAM": ["GM", "GMS", "G"],
        "JULIES": ["JULIE S", "JULIES", "JULIE", "JULI", "JULYS"],
        "SANDWICH": ["S/WICH", "SWICH", "SANDWICHES"],
        "LEMOND": ["LE-MOND"],
        "DOUBLE STUF": ["DOUBLESTUF", "DOUBLE STUFF", "DBLE STUF", "DBLE STUFF"],
        "CRUNCHY BITES": ["CRUNCHIES", "CRUNCHY"],
        "OAT 25": ["OAT25"],
    }
    for primary, aliases in syns.items():
        for alias in aliases:
            # Use regex to replace whole word only to avoid partial matches
            # 🚨 WORD BOUNDARY GUARD (\b) prevents 'CARAMELISED' matching 'CARAMEL'
            s = re.sub(rf'\b{alias}\b', primary, s)
    return s

def calculate_similarity(a, b):
    """Calculate fuzzy string similarity with synonym normalization."""
    # Normalize synonyms before comparison
    norm_a = normalize_synonyms(a)
    norm_b = normalize_synonyms(b)
    return SequenceMatcher(None, norm_a, norm_b).ratio()

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

async def process_nielsen_dataframe(df, sheet_name, request=None):
    """
    Core logic for Flow 1: Processes a single DataFrame and saves to single_stock_data.
    """
    FIXED_SHEET_NAME = "wersel_match"
    
    # ✅ FIX: Sort DataFrame for deterministic processing
    sort_cols = []
    for col in ['UPC', 'ITEM', 'MARKETS', 'MPACK', 'Facts']:
        if col in df.columns:
            sort_cols.append(col)
    
    if sort_cols:
        df = df.sort_values(by=sort_cols).reset_index(drop=True)
    
    # KEY COLUMN IDENTIFICATION
    col_map = {c.upper().strip(): c for c in df.columns}
    
    # Must have UPC
    if "UPC" not in col_map:
        return {"error": "Missing UPC column"}
        
    upc_col = col_map["UPC"]
    market_col = col_map.get("MARKETS")
    mpack_col = col_map.get("MPACK")
    facts_col = col_map.get("FACTS")
    size_col = col_map.get("NRMSIZE")
    item_col = col_map.get("ITEM") or col_map.get("PRODUCT NAME") or col_map.get("DESCRIPTION")
    
    # Store raw data - Preserve all rows
    raw_coll = get_collection(RAW_DATA_COL)
    
    rows_to_insert = []
    df_raw = df.replace({pd.NA: None, float('nan'): None})
    for row in df_raw.to_dict("records"):
        row["sheet_name"] = FIXED_SHEET_NAME
        rows_to_insert.append(row)
        
    if rows_to_insert:
        raw_coll.insert_many(rows_to_insert)
    
    # Identify monthly/metric columns
    PROTECTED_COLS = ["MARKETS", "MARKET", "MPACK", "PACK", "BRAND", "ITEM", "UPC", "FACTS", "FACT", "NRMSIZE", "SIZE"]
    
    monthly_cols = [c for c in df.columns if 
        any(m in str(c).upper() for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "W/E", "MAT"])
        and str(c).upper().strip() not in PROTECTED_COLS
    ]
    
    ignore_cols = monthly_cols + [upc_col]
    if facts_col: ignore_cols.append(facts_col)
    
    descriptive_cols = [c for c in df.columns if c not in ignore_cols]
    
    # Filter valid UPCs
    df = df[df[upc_col].notnull()].copy()
    
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

    brand_col = col_map.get("BRAND")
    flavour_col = col_map.get("FLAVOUR") or col_map.get("FLAVOR")
    
    if item_col:
        df["_group_item_clean"] = df[item_col].apply(simple_clean_item)
        group_keys.append("_group_item_clean")
        
    if brand_col:
        df[brand_col] = df[brand_col].fillna(fill_val)
        group_keys.append(brand_col)
    
    if flavour_col:
        df[flavour_col] = df[flavour_col].fillna(fill_val)
        group_keys.append(flavour_col)

    variant_col = col_map.get("VARIANT")
    if variant_col:
        df[variant_col] = df[variant_col].fillna(fill_val)
        group_keys.append(variant_col)

    if size_col:
        df[size_col] = df[size_col].fillna(fill_val)
        group_keys.append(size_col)

    print(f"[{sheet_name}] Creating groups...")
    groups_list = list(df.groupby(group_keys))
    
    def process_single_group(group_data):
        group_ids, group = group_data
        buckets = [group.to_dict('records')]
        bucket_records = []
        for bucket in buckets:
            base_row = bucket[0]
            merged_count = len(bucket)
            product_names = [r[item_col] for r in bucket] if item_col else [f"UPC_{base_row[upc_col]}"] * merged_count
            
            merged_record = {"UPC": base_row[upc_col]}
            if market_col: merged_record[market_col] = base_row[market_col]
            if mpack_col: merged_record[mpack_col] = base_row[mpack_col]
            if facts_col: merged_record[facts_col] = base_row[facts_col]
            
            for col in descriptive_cols:
                if col in base_row and col not in merged_record:
                    merged_record[col] = base_row[col]
            
            for col in monthly_cols:
                total = 0.0
                if col in base_row:
                    for r in bucket:
                        val = r.get(col, 0)
                        try:
                            f_val = float(val)
                            if not math.isnan(f_val):
                                total += f_val
                        except: pass
                merged_record[col] = total
            
            brand = merged_record.get("BRAND", "UNKNOWN")
            merge_id = f"{brand}_{uuid.uuid4().hex}"
            
            merge_rule_parts = ["UPC"]
            if market_col: merge_rule_parts.append("Market")
            if mpack_col: merge_rule_parts.append("MPack")
            if facts_col: merge_rule_parts.append("Facts")
            if size_col and merged_count > 1: merge_rule_parts.append("Size") # Removed (5g)
            
            merged_record["merge_id"] = merge_id
            merged_record["merge_items"] = product_names
            merged_record["ITEM"] = product_names[0] if product_names else f"UPC_{base_row[upc_col]}"
            merged_record["merged_from_docs"] = merged_count
            merged_record["merge_rule"] = " + ".join(merge_rule_parts)
            merged_record["merged_upcs"] = [str(base_row[upc_col])]
            merged_record["merge_level"] = "NO_MERGE" if merged_count == 1 else f"MERGED_{merged_count}_VARIANTS"
            merged_record["sheet_name"] = "wersel_match"
            bucket_records.append(merged_record)
        
        merge_logs = []
        for rec in bucket_records:
            if rec.get("merged_from_docs", 1) > 1:
                merge_logs.append({
                    "merged_product": rec.get("ITEM"),
                    "upc": rec.get("UPC"),
                    "size": rec.get(size_col) if size_col else "N/A",
                    "merged_from": rec.get("merge_items"),
                    "count": rec.get("merged_from_docs")
                })
        return bucket_records, merge_logs

    single_stock_records = []
    all_merge_logs = []
    batch_size = 1000
    total_groups = len(groups_list)
    
    print(f"[{sheet_name}] Starting batch-wise parallel processing...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        for batch_start in range(0, total_groups, batch_size):
            if request and await request.is_disconnected():
                print(f"Stopping Flow 1: Client disconnected during batch processing")
                return {}
            batch_end = min(batch_start + batch_size, total_groups)
            batch_results = list(executor.map(process_single_group, groups_list[batch_start:batch_end]))
            for group_records, group_logs in batch_results:
                single_stock_records.extend(group_records)
                all_merge_logs.extend(group_logs)
            await asyncio.sleep(0)
    
    if all_merge_logs:
        try:
            with open("flow1_merges_debug.json", "w", encoding="utf-8") as f:
                json.dump(all_merge_logs, f, indent=2)
            print(f"[{sheet_name}] Saved {len(all_merge_logs)} merge logs to flow1_merges_debug.json")
        except Exception as e:
            print(f"Error saving merge logs: {e}")

    print(f"[{sheet_name}] Parallel processing complete: {len(single_stock_records)} total records")

    if single_stock_records:
        single_stock_coll = get_collection(SINGLE_STOCK_COL)
        single_stock_coll.delete_many({"sheet_name": "wersel_match"})
        total_records = len(single_stock_records)
        
        print(f"[{sheet_name}] Saving {total_records} records to MongoDB...")

        for i in range(0, total_records, 5000):
            batch = single_stock_records[i:i + 5000]
            try:
                single_stock_coll.insert_many(batch, ordered=False)
            except Exception as e:
                print(f"[{sheet_name}] Batch insert error: {e}")
                for record in batch:
                    try:
                        single_stock_coll.insert_one(record)
                    except:
                        pass
            progress = min(i + 5000, total_records)
            if progress % 10000 == 0 or progress == total_records:
                print(f"[{sheet_name}] MongoDB: Saved {progress}/{total_records} ({(progress/total_records*100):.1f}%)")
        print(f"[{sheet_name}] Saved {total_records} records to MongoDB")
    
    return {"raw_count": len(df), "single_stock_count": len(single_stock_records)}

async def process_excel_flow_1(file_contents, request=None):
    """
    Flow 1: Strict UPC + Attribute merging with Size Tolerance.
    Supports Excel (.xlsx, .xls) and CSV (.csv) files.
    Groups by UPC, Markets, MPACK, Facts to separate variants/metrics.
    Uses Exact Size matching (no tolerance) for grouping.
    """
    import io
    
    # ✅ STEP 0: Reset Database for Fresh Upload (Single-Session Flow)
    reset_main_collections()
    
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
        
        sheets_info[sheet_name] = await process_nielsen_dataframe(df, sheet_name, request)
    
    return sheets_info

async def reprocess_flow_1_from_db():
    """
    Automated Phase for full re-run. Reads from raw_data and populates single_stock_data.
    """
    print("Reprocessing Flow 1 from DB (raw_data)...")
    raw_coll = get_collection(RAW_DATA_COL)
    docs = list(raw_coll.find({}))
    if not docs:
        print("⚠️ No raw data found in DB.")
        return
    
    df = pd.DataFrame(docs)
    # Remove MongoDB _id if present
    if "_id" in df.columns: df = df.drop(columns=["_id"])
    
    # Process
    await process_nielsen_dataframe(df, "Reprocess_All")
    print("Reprocessing Flow 1 Complete.")


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
        data = cached["result"]
        # Force re-apply guards even to cached data to ensure consistency after rule updates
        data = apply_llm_rule_guards(item, data)
        llm_cache[item] = data
        return data
    
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
  - {COK, CHOC, CHOCO, COKLAT, CHOKLAT, CHOKIT, COKLIT, CHCO} -> CHOCOLATE 
  (Only when used alone. Do NOT collapse compound flavours like:
   CHOC CHIP, DARK CHOC, WHITE CHOC, SALTED CHOC, MILK CHOC.)
  - {BAN, BNNA, BANANA} -> BANANA
  - {VAN, VNL, VENLLA, VANILLA} -> VANILLA
  - {PNUT, PNT, PEANUT} -> PEANUT
  - {NPLTNE, NEAPOLITAN} -> NEAPOLITAN
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
  - {CRM, CREME, CREAM} -> CREAM

- PRODUCT FORMS (IMPORTANT: Keep these distinct):
  - {BISK, BSC, BISCUIT, CKI, COOKIE} -> BISCUIT / COOKIE
  - {WAF, WFR, WAFER} -> WAFER
  - {STK, STICK, PRETZ, TOPPO, PEPERO, POCKY} -> STICK
  - {ROL, ROLL} -> ROLL
  - {PCH, POUCH} -> POUCH
  - {SNK, SNACK, CAPLICO, CHOCOROOM} -> SNACK / CHOCOROOM
  - {DONUT, DNNT} -> DONUT
  - {HIPPO, TRONKY} -> Keep specific form (HIPPO / TRONKY)
  - {FINGER, ROUND, TRIANGLE} -> Keep shape as Form
  - {MARIE, MRE} -> MARIE
  - {CRACKER, CRK, CRACKERS, CRACK} -> CRACKER
  - {YANYAN, YAN YAN} -> YAN YAN
  - {HELLOPANDA, HELLO PANDA} -> HELLO PANDA
  - {LUCKY STICK} -> LUCKY STICK
  - {ASSORTED, ASST, TIN, BOX, PARTY, SELECTION} -> ASSORTED
  - {DIP DIP, DIPDIP, DIPPING, CUP} -> DIP DIP / CUP (Treat as distinct product form)
  - {BUBBLE PUFF, BUBBLEPUFF} -> BUBBLE PUFF (Treat as distinct product form)

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
  - {ORI} -> Treat as Brand "ORI" only if it appears at the START of the description. Otherwise, ignore it or check for "ORIGINAL".
  - {HUP SENG, HUPSENG, HS} -> HUP SENG
  - {JULIES, JULIE, JULI, JULYS} -> JULIES
  - {BIOGREEN, BIO GREEN} -> BIO GREEN
  - {LEE, LEE BRANDS} -> LEE BRANDS
  - {MUNCHYS, MUNCHY} -> MUNCHYS
  - {NABATI, RICHEESE, NEXTAR} -> NABATI (RICHEESE and NEXTAR are Nabati sub-brands/product lines, not standalone brands. Always set brand=NABATI.)

- PACKAGING:
  - {CAN, CN} -> CAN
  - {BTL, BT} -> BOTTLE
  - {VP, V.PACK} -> MULTIPACK
  - {RTE} -> READY TO EAT

### 🍯 SUGAR & DIETARY FLAGS:
- {SF, NO SUGAR, WITHOUT SUGAR, S.FREE, ZERO SUGAR} -> SUGAR FREE
- {NORMAL} -> NORMAL (flavour)
- {ORIGINAL} -> ORIGINAL (flavour, do NOT convert to NORMAL)
- {REGULAR} -> REGULAR (variant only. Never treat as flavour.)

### 🏷️ VARIANTS & SUB-FLAVOURS (CRITICAL):
- Distinguish between REGULAR versions and special ones like {MINI, GIANT, SNOWY, EXTRA, GOLD, PREMIUM, GOKUBOSO, FESTIVE}.
- If a product has "SNOWY", mark variant as "SNOWY".
- If it's a standard one, mark variant as "REGULAR".

### 🍯 FLAVOUR & VARIANT RULES (CRITICAL):
1. **NO SIMPLIFICATION**: Never reduce a compound flavour to a base one.
2. **PRESERVE ALL COMPONENTS**: If a product has multiple flavor components (e.g., SEA SALT, PISTACHIO, CARAMEL), BOTH must be in the "flavour" string.
3. **ORDER MATTERS**: Keep the sequence of flavors as much as possible.
4. **DISTINCT PROFILES**: Treat these as completely DIFFERENT products:
   - "SEA SALT PISTACHIO CHOCOLATE CHIP" != "DOUBLE CHOCOLATE CHIP"
   - "ROASTED HAZELNUT CHOCOLATE CHIP" != "CHOCOLATE CHIP"
   - "SALTED CARAMEL" != "CARAMEL"
   - "MACADAMIA WHITE CHOCOLATE" != "CRANBERRY WHITE CHOCOLATE"

5. **SPECIFIC EXCLUSIONS**: 
   - Never ignore ingredients like "HAZELNUT", "PISTACHIO", "ALMOND", "SEA SALT" just because "CHOCOLATE" is also present.
   - If multiple flavours are present, extract the full specific flavour string (e.g., "STRAWBERRY & BLACKCURRANT").
   - Do NOT combine flavours unless the compound is an established flavour name.

### Few-Shot Examples for Accuracy:
1. Input: "MUNCHYS OATKRUNCH S/BERRY&B/CURR 390G"
   Output: {
  "brand": "MUNCHYS",
  "product_line": "OAT KRUNCH",
  "flavour": "STRAWBERRY & BLACKCURRANT",
  "variant": "REGULAR",
  "size": "390G",
  "product_form": "BISCUIT",
  "is_sugar_free": false,
  "base_item": "MUNCHYS OAT KRUNCH BISCUIT STRAWBERRY & BLACKCURRANT 390G",
  "confidence": 1.0
}

2. Input: "SKINNY BAKERS COOKIE SLTED CRML CHOC CHIP CKS 80G"
   Output: {
  "brand": "THE SKINNY BAKER",
  "product_line": "COOKIES",
  "flavour": "SALTED CARAMEL CHOCOLATE CHIP",
  "variant": "REGULAR",
  "size": "80G",
  "product_form": "COOKIE",
  "is_sugar_free": false,
  "base_item": "THE SKINNY BAKER COOKIE SALTED CARAMEL CHOCOLATE CHIP 80G",
  "confidence": 1.0
}

3. Input: "THE SKINNY BAKER SKINNY BAKERS S/SALT PISTACHIO CHOC CHIP CKS 150G"
   Output: {
  "brand": "THE SKINNY BAKER",
  "product_line": "SKINNY BAKERS",
  "flavour": "SEA SALT PISTACHIO CHOCOLATE CHIP",
  "variant": "REGULAR",
  "size": "150G",
  "product_form": "COOKIE",
  "is_sugar_free": false,
  "base_item": "THE SKINNY BAKER SKINNY BAKERS COOKIE SEA SALT PISTACHIO CHOCOLATE CHIP 150G",
  "confidence": 1.0
}

4. Input: "LOTTE PEPERO SNOWY ALMOND 32G"
   Output: {
  "brand": "LOTTE",
  "product_line": "PEPERO",
  "flavour": "ALMOND",
  "variant": "SNOWY",
  "size": "32G",
  "product_form": "STICK",
  "is_sugar_free": false,
  "base_item": "LOTTE PEPERO STICK SNOWY ALMOND 32G",
  "confidence": 1.0
}

5. Input: "GLICO POCKY CHOCOLATE GOKUBOSO 71G"
   Output: {
  "brand": "GLICO",
  "product_line": "POCKY",
  "flavour": "CHOCOLATE",
  "variant": "GOKUBOSO",
  "size": "71G",
  "product_form": "STICK",
  "is_sugar_free": false,
  "base_item": "GLICO POCKY STICK CHOCOLATE GOKUBOSO 71G",
  "confidence": 1.0
}

6. Input: "NABATI NEXTAR BROWNIES CHOCOLATE 272G"
   Output: {
  "brand": "NABATI",
  "product_line": "NEXTAR BROWNIES",
  "flavour": "CHOCOLATE",
  "variant": "REGULAR",
  "size": "272G",
  "product_form": "BISCUIT",
  "is_sugar_free": false,
  "base_item": "NABATI NEXTAR BROWNIES BISCUIT CHOCOLATE 272G",
  "confidence": 1.0
}

6b. Input: "NABATI FESTIVE NEXTAR BROWNIES 272G"
    Output: {
  "brand": "NABATI",
  "product_line": "NEXTAR BROWNIES",
  "flavour": "CHOCOLATE",
  "variant": "REGULAR",
  "size": "272G",
  "product_form": "BISCUIT",
  "is_sugar_free": false,
  "base_item": "NABATI NEXTAR BROWNIES BISCUIT CHOCOLATE 272G",
  "confidence": 1.0
}

6c. Input: "NABATI RICHEESE WAFER 145GM"
    Output: {
  "brand": "NABATI",
  "product_line": "RICHEESE",
  "flavour": "CHEESE",
  "variant": "REGULAR",
  "size": "145G",
  "product_form": "WAFER",
  "is_sugar_free": false,
  "base_item": "NABATI RICHEESE WAFER CHEESE 145G",
  "confidence": 1.0
}

6d. Input: "NABATI NEXTAR STRAWBERRY 106G"
    Output: {
  "brand": "NABATI",
  "product_line": "NEXTAR",
  "flavour": "STRAWBERRY",
  "variant": "REGULAR",
  "size": "106G",
  "product_form": "BISCUIT",
  "is_sugar_free": false,
  "base_item": "NABATI NEXTAR BISCUIT STRAWBERRY 106G",
  "confidence": 1.0
}

7. Input: "HUP SENG CRM CRACKER 428GMX12"
   Output: {
  "brand": "HUP SENG",
  "product_line": "CREAM CRACKERS",
  "flavour": "NORMAL",
  "variant": "REGULAR",
  "size": "428GMX12",
  "product_form": "CRACKER",
  "is_sugar_free": false,
  "base_item": "HUP SENG CREAM CRACKERS 428GMX12",
  "confidence": 1.0
}

8. Input: "JULIE CHEESE STICKS 4.5KG"
   Output: {
  "brand": "JULIES",
  "product_line": "CHEESE STICKS",
  "flavour": "CHEESE",
  "variant": "REGULAR",
  "size": "4500G",
  "product_form": "STICK",
  "is_sugar_free": false,
  "base_item": "JULIES STICK CHEESE 4500G",
  "confidence": 1.0
}

9. Input: "BOURBON BUTTER COOKIES 9PCS 100G"
   Output: {
  "brand": "BOURBON",
  "product_line": "COOKIES",
  "flavour": "BUTTER",
  "variant": "REGULAR",
  "size": "100G",
  "product_form": "BISCUIT",
  "is_sugar_free": false,
  "base_item": "BOURBON BISCUIT BUTTER 100G",
  "confidence": 1.0
}

10. Input: "BOURBON GOKOKU NO BISCUT 32P 133G"
    Output: {
  "brand": "BOURBON",
  "product_line": "GOKOKU NO BISCUIT",
  "flavour": "NORMAL",
  "variant": "REGULAR",
  "size": "133G",
  "product_form": "BISCUIT",
  "is_sugar_free": false,
  "base_item": "BOURBON GOKOKU NO BISCUIT 133G",
  "confidence": 1.0
}

11. Input: "BOURBON CEBEURE (14 X 8 G) 112 G"
    Output: {
  "brand": "BOURBON",
  "product_line": "CEBEURE",
  "flavour": "NORMAL",
  "variant": "REGULAR",
  "size": "112G",
  "product_form": "BISCUIT",
  "is_sugar_free": false,
  "base_item": "BOURBON CEBEURE 112G",
  "confidence": 1.0
}

### GOAL:
Extract "brand", "flavour", "variant", "size", "product_line", "product_form", "is_sugar_free" and "base_item" as JSON.

IMPORTANT: 
1. The "flavour" field MUST contain ALL flavor-related keywords (e.g., SEA SALT, PISTACHIO, HAZELNUT, CARAMEL). Never omit them.
2. **STRICT LITERAL SIZE EXTRACTION**: The "size" field must be extracted in a standardized numeric form if possible (e.g., convert '4.5KG' to '4500G', '320ML' to '320ML'). For simple cases like '130G', keep it as '130G'.
3. **SPELING TOLERANCE**: Always normalize brand names to their most common full form (e.g., 'JULIE' -> 'JULIES').
4. **MPACK Awareness**: If the description mentions a pack count (e.g., 12S, 12X, *12, X12), include it in the size string exactly as written.
5. **PUNCTUATION REMOVAL**: NEVER include apostrophes (') or backticks (`) in brand or product_line names. (e.g. "O'SOY" -> "OSOY").
6. **PIECE COUNT REMOVAL**: Piece counts (e.g., 9PCS, 10 PCS) are NOT part of the product line, flavor, or variant.
7. **PLURAL NORMALIZATION**: Always use singular form for "product_form" and "product_line" if possible (e.g., "CRACKERS" -> "CRACKER", "COOKIES" -> "COOKIE", "STICKS" -> "STICK").

Base item must follow this structure:
BRAND + PRODUCT_LINE (if any) + PRODUCT_FORM + FLAVOUR + VARIANT (if not REGULAR) + SIZE

"""
    
    user_prompt = f"""
ITEM DESCRIPTION: "{item}"

Return JSON only:
{{
  "brand": "Standardized Brand Name (e.g., NABATI, MEIJI)",
  "product_line": "Specific Sub-Brand or Line (e.g., NEXTAR, NEXTAR BROWNIES, RICHEESE, MALKIST, YAN YAN, HELLO PANDA, OAT KRUNCH, OAT 25, GOLDEN CRACKER, TIM TAM, PEPERO). IMPORTANT: For NABATI brand - RICHEESE and NEXTAR are product lines (not brand names). FESTIVE is a marketing/seasonal descriptor, NOT a product line - ignore it. Note: 'MINI OREO' and 'OREO MINI' are BOTH 'product_line: OREO' with 'variant: MINI'.",
  "flavour": "Standardized Flavour Name. Note: ORIGINAL, VANILLA, and NORMAL are considered equivalent for most biscuits (especially OREO).",
  "variant": "Standardized Variant (e.g., REGULAR, SNOWY, MINI, GOLD, GOKUBOSO). NOTE: Do NOT use FESTIVE as variant. FESTIVE is seasonal packaging only - always output REGULAR for Nabati FESTIVE items.",
  "product_form": "Standardized Form (e.g., STICK, WAFER, BISCUIT, COOKIE, ROLL)",
  "is_sugar_free": boolean,
  "size": "Standardized Size (e.g., 320ML, 500G)",
  "base_item": "Standardized Full Generic Name (Include weight)",
  "removed_marketing_terms": ["list", "of", "removed", "terms"],
  "confidence": 0.0 to 1.0
}}
"""
    
    try:
        # ✅ Use OpenAI-only client for Flow 2 (faster, no rate limits)
        raw_content = flow2_client.chat_completion(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0
        )
        
        raw_content = raw_content.strip()
        
        # Handle empty response
        if not raw_content or raw_content == '{}':
            print(f"Empty LLM response for '{item}' - using fallback")
            raise ValueError("Empty response from LLM")
        
        # ✅ FIX: Extract only the JSON object, ignore extra text
        # Find the first { and last } to extract just the JSON
        start_idx = raw_content.find("{")
        end_idx = raw_content.rfind("}")
        
        if start_idx != -1 and end_idx != -1:
            json_str = raw_content[start_idx:end_idx+1]
        else:
            json_str = raw_content
        
        data = json.loads(json_str)
        
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
            "variant": "REGULAR",
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
            "product_line": "",
            "flavour": "NORMAL",
            "variant": "REGULAR",
            "size": "",
            "product_form": "",
            "base_item": item,
            "is_sugar_free": False,
            "removed_marketing_terms": [],
            "confidence": 0.0
        }
    
    # 🚨 RULE-LAYER GUARDS (USE ONLY AS FALLBACK FOR GENERIC/MISSING DATA)
    
    # 1. Brand-First Protection (For "ORI")
    trimmed_item = item.strip().upper()
    if trimmed_item.startswith("ORI "):
        if not data.get("brand") or data["brand"] in ["ORIGINAL", "UNKNOWN", ""]:
            data["brand"] = "ORI"
            if data.get("flavour") == "ORI":
                data["flavour"] = "NORMAL"

    # Only apply flavor/variant guards if the LLM output is generic or empty
    current_flv = str(data.get("flavour", "")).upper()
    current_var = str(data.get("variant", "")).upper()
    
    is_generic = current_flv in ["NORMAL", "UNKNOWN", "", "NONE", "CHOCOLATE", None]
    
    clean_raw = normalize_synonyms(item).upper()

    if is_generic:
        # High-priority compound descriptors
        compounds = [
            "SEA SALT PISTACHIO", "SEA SALT HAZELNUT", "SALTED CARAMEL", 
            "DARK CHOCOLATE", "WHITE CHOCOLATE", "MILK CHOCOLATE", 
            "SEA SALT CHOC CHIP", "SALTED VANILLA", "CHUNKY HAZELNUT",
            "COOKIES & CREAM", "DOUBLE CHOCOLATE", "SOUR CREAM & ONION"
        ]
        for cp in compounds:
            if cp in clean_raw:
                data["flavour"] = cp
                print(f"Rule Guard: Restored compound flavour '{cp}' for '{item}'")
                break
        
        # Basic flavor fallback only if STILL generic after compound check
        if data["flavour"] in ["NORMAL", "UNKNOWN", "", None]:
            basic_flavours = [
                "STRAWBERRY", "CHOCOLATE", "VANILLA", "CHEESE", "BUTTER", "ALMOND", 
                "HAZELNUT", "LEMON", "DURIAN", "PINEAPPLE", "COFFEE", "ORANGE"
            ]
            for bf in basic_flavours:
                if bf in clean_raw:
                    data["flavour"] = bf
                    break

    # Apply final guards before returning/caching
    data = apply_llm_rule_guards(item, data)
    
    # Save to persistent cache and in-memory cache
    save_to_llm_cache(item, data)
    llm_cache[item] = data
    return data

def apply_llm_rule_guards(item, data):
    """
    Apply mandatory rules to LLM output to fix known inconsistencies.
    """
    clean_raw = normalize_synonyms(item).upper()
    
    # 0. Julie's & Oreo Specific Product Line Guards (Apply before anything else)
    if "GOLDEN CRACKER" in clean_raw:
        data["product_line"] = "GOLDEN CRACKER"
        data["variant"] = "REGULAR"
        data["flavour"] = "NORMAL"
        
    if "OAT 25" in clean_raw or "OAT25" in clean_raw:
        data["product_line"] = "OAT 25"

    if "OREO" in clean_raw:
        data["brand"] = "OREO" # Ensure Oreo is the brand
        data["confidence"] = 1.0 # Force high confidence for Oreo items to ensure merging
        
        # Force Form for consistency
        if "WAFER ROLL" in clean_raw:
            data["product_line"] = "WAFER ROLL"
            data["product_form"] = "ROLL"
        else:
            data["product_form"] = "COOKIE" # Standard for regular Oreos
        
        # Merge Original and Vanilla as requested (they are considered same flavor contextually)
        if str(data.get("flavour", "")).upper() in ["ORIGINAL", "VANILLA", "NORMAL", "UNKNOWN", "VAN", "ORG"]:
            data["flavour"] = "ORIGINAL/VANILLA"
        
        # Merge Limited Edition into Regular
        if any(x in clean_raw for x in ["LIM EDT", "LIMITED EDITION", "LTD EDT"]):
            data["variant"] = "REGULAR"
            
        # Ensure Double Stuf consistency
        if "DOUBLE STUF" in clean_raw or "DOUBLESTUF" in clean_raw:
            data["product_line"] = "DOUBLE STUF"
            
        if "MINI" in clean_raw:
            data["variant"] = "MINI"
            data["product_line"] = "OREO" # Standard Oreo line for minis
            
        if "RED VELVET" in clean_raw:
            data["product_line"] = "OREO" # Standard Oreo line
            data["flavour"] = "RED VELVET"

    if "GOLDEN CRACKER" in clean_raw:
        data["product_line"] = "GOLDEN CRACKER"
        data["variant"] = "REGULAR"
        data["flavour"] = "NORMAL"
        data["confidence"] = 1.0
        
    if "OAT 25" in clean_raw or "OAT25" in clean_raw:
        data["product_line"] = "OAT 25"
        data["confidence"] = 1.0

    clean_raw = normalize_synonyms(item).upper()
    
    # 1. Brand Normalization
    final_brand = str(data.get("brand", "")).upper().strip()
    brand_map = {
        "JULIE": "JULIES", "JULYS": "JULIES", "JULI": "JULIES", "JULIE S": "JULIES",
        "HUPSENG": "HUP SENG", "HS": "HUP SENG",
        # ✅ NABATI sub-brand normalization: RICHEESE and NEXTAR are Nabati product lines
        "RICHEESE": "NABATI", "NEXTAR": "NABATI",
    }
    if final_brand in brand_map:
        data["brand"] = brand_map[final_brand]

    # ✅ NABATI Guard: If item contains NABATI/RICHEESE/NEXTAR and brand is empty/wrong, force NABATI
    if any(kw in clean_raw for kw in ["NABATI", "RICHEESE", "NEXTAR"]):
        if not final_brand or final_brand in ["UNKNOWN", "NORMAL", "", "RICHEESE", "NEXTAR"]:
            data["brand"] = "NABATI"
    
    if clean_raw.startswith("JULIE") and (not final_brand or final_brand in ["UNKNOWN", "NORMAL", ""]):
        data["brand"] = "JULIES"

    # ✅ BIO GREEN Normalization
    if "BIOGREEN" in clean_raw or "BIO GREEN" in clean_raw:
        if not final_brand or final_brand in ["UNKNOWN", "NORMAL", "OTHERS", ""]:
            data["brand"] = "BIO GREEN"

    # ✅ LEE BRANDS Normalization
    if "LEE" in clean_raw:
        if not final_brand or final_brand in ["UNKNOWN", "NORMAL", "LEE", ""]:
            data["brand"] = "LEE BRANDS"

    # 2. Size Normalization (Standardize units and remove trailing junk)
    current_size = str(data.get("size", "")).upper().replace(" ", "")
    # Normalize GM -> G
    current_size = current_size.replace("GM", "G")
    # Remove trailing 'P' often from POUCH if it follows a number (e.g., 20.4GP -> 20.4G)
    current_size = re.sub(r'(\d)GP$', r'\1G', current_size)
    
    data["size"] = current_size

    # KG to G conversion for consistency (e.g., 4.5KG -> 4500G)
    if "KG" in current_size:
        try:
            val_match = re.search(r'(\d*\.?\d+)\s*KG', current_size)
            if val_match:
                val = float(val_match.group(1))
                data["size"] = f"{int(val * 1000)}G"
        except: pass

    # 3. Punctuation Strip Fallback (Ensure no ' or ` in fields)
    for field in ["brand", "product_line", "flavour", "variant", "product_form"]:
        if field in data and isinstance(data[field], str):
            data[field] = data[field].replace("'", "").replace("`", "")
            # ✅ Strip piece counts from fields (e.g. "COOKIES 9PCS" -> "COOKIES")
            data[field] = re.sub(r'\b\d+\s*PCS\b', '', data[field], flags=re.IGNORECASE).strip()
            # ✅ Plural Normalization (e.g. CRACKERS -> CRACKER)
            for plur, sing in [("CRACKERS", "CRACKER"), ("COOKIES", "COOKIE"), ("STICKS", "STICK")]:
                data[field] = re.sub(rf'\b{plur}\b', sing, data[field], flags=re.IGNORECASE).strip()

    # 4. Flavour/Variant Fallbacks
    
    # ✅ BOURBON Specific Guards
    if "BOURBON" in clean_raw:
        data["brand"] = "NABATI" # User confirmed Bourbon items are under Nabati cluster
        # Fix Gokoku No Biscuit typo and recognize line
        if "GOKOKU" in clean_raw:
            data["product_line"] = "GOKOKU NO BISCUIT"
            data["product_form"] = "BISCUIT"
            data["variant"] = "REGULAR"
            data["flavour"] = "NORMAL"
            data["confidence"] = 1.0
        
        if "CEBEURE" in clean_raw:
            data["product_line"] = "CEBEURE"
            data["product_form"] = "BISCUIT"
            data["variant"] = "REGULAR"
            data["flavour"] = "NORMAL"
            data["confidence"] = 1.0

    # ✅ LEXUS Specific Guards
    if "LEXUS" in clean_raw or "LEXUS" in item.upper():
        data["brand"] = "LEXUS"
        data["product_line"] = "LEXUS" # Ensure product_line is NOT NONE to avoid LOW_CONF divergence
        data["confidence"] = 1.0

        if "CHOCO COATED" in clean_raw or "CHOCO COATED" in item.upper():
            data["flavour"] = "CHOCOLATE COATED"
            data["product_form"] = "BISCUIT"
            
        # Fix hallucinated 'OAT' for regular Lexus biscuits
        # Use word boundary to avoid matching 'COATED'
        if data.get("flavour") == "OAT" and not re.search(r'\bOAT\b', clean_raw):
            data["flavour"] = "NORMAL"

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
        [str(d.get("UPC")) for d in group_docs if d.get("UPC")]
    ))

    
    base["merged_from_docs"] = sum(d.get("merged_from_docs", 1) for d in group_docs)
    
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
    s = str(name).upper().replace("-", "") # 🚨 Strip hyphens to match 'PRE-BALANCE' with 'PREBALANCE'
    # Normalize synonyms FIRST
    s = normalize_synonyms(s)
    # Remove very common noise words only
    for word in ["ITEM", "PACK", "FLAVOUR", "FLV", "BRAND", "PCS"]:
        s = s.replace(word, " ")
    # Take alphanumeric words only and sort them
    words = sorted(list(set(re.findall(r'[A-Z0-9]+', s))))
    return "".join(words)


async def process_llm_mastering_flow_2(sheet_name, request=None):
    """
    Flow 2: LLM Mastering.
    Reads from single_stock_data, creates master_stock_data with LLM-extracted attributes.
    """
    FIXED_SHEET_NAME = "wersel_match"
    src_col = get_collection(SINGLE_STOCK_COL)
    tgt_col = get_collection(MASTER_STOCK_COL)
    
    # Process items that match our fixed sheet name
    docs = list(src_col.find({"sheet_name": FIXED_SHEET_NAME}))
    print(f"Loaded {len(docs)} docs from MongoDB ({SINGLE_STOCK_COL})")

    
    groups = {}
    single_docs = []
    
    # 1. Discovery Phase: Extract unique items and fetch attributes in parallel
    print(f"Discovery Phase: Extracting unique attributes for {len(docs)} items...")

    unique_items = list(set([d.get("ITEM") for d in docs if d.get("ITEM")]))
    
    # ✅ FIX: Map original item to context-aware item (Prepend Brand if missing)
    # This helps LLM identify Family (e.g. "POCKY") even if missing in description
    item_to_context = {}
    for d in docs:
        it = d.get("ITEM")
        if it not in item_to_context:
            br = str(d.get("BRAND", "")).strip()
            # Only prepend if brand is not already in the item description
            if br and br.upper() not in it.upper():
                item_to_context[it] = f"{br} {it}"
            else:
                item_to_context[it] = it
    
    # ✅ Optimization: Group unique items by their "Clean Keys" to reduce redundant LLM calls
    clean_groups = {} # {clean_key: [original_items]}
    for item in unique_items:
        ckey = simple_clean_item(item)
        clean_groups.setdefault(ckey, []).append(item)
    
    # Representative items to send to LLM
    representative_items = []
    ckey_to_rep = {} # {clean_key: representative_item}
    
    for ckey, items in clean_groups.items():
        # Choose the longest name as representative (usually most descriptive)
        rep = max(items, key=len)
        representative_items.append(rep)
        ckey_to_rep[ckey] = rep

    norm_map = {} # {original_item: result}
    rep_results = {} # {representative_item: result}
    
    # Process in batches to avoid rate limits
    batch_size = 500
    total_batches = (len(representative_items) + batch_size - 1) // batch_size
    
    print(f"Processing {len(representative_items)} representative items (from {len(unique_items)} total unique) in {total_batches} batches...")
    
    # ✅ Strategy 2: Pre-load cache from MongoDB
    try:
        cache_coll = get_collection("LLM_CACHE_STORAGE")
        # Pre-load only for representative context items
        context_reps = [item_to_context.get(it, it) for it in representative_items]
        existing_cache_docs = list(cache_coll.find({"item": {"$in": context_reps}}))
        existing_cache = {}
        for doc in existing_cache_docs:
            item_name = doc["item"]
            res = doc["result"]
            # RE-APPLY GUARDS to cached data to ensure new force rules take effect
            res = apply_llm_rule_guards(item_name, res)
            existing_cache[item_name] = res
            
        llm_cache.update(existing_cache)
        print(f"Pre-loaded {len(existing_cache)} items from persistent cache with latest rule guards applied.")
    except Exception as e:
        print(f"Error pre-loading cache: {e}")

    for batch_num in range(total_batches):
        if batch_num % 10 == 0 and request and await request.is_disconnected():
            print(f"Stopping Flow 2: Client disconnected before batch {batch_num + 1}")
            return {"status": "Stopped | Client disconnected"}

        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(representative_items))
        batch_reps = representative_items[start_idx:end_idx]
        
        # ✅ Use context-aware names (with Brand) for LLM
        # Map: original_item -> context_item
        batch_map = {it: item_to_context.get(it, it) for it in batch_reps}
        
        print(f"Batch {batch_num + 1}/{total_batches}: Calling LLM for {len(batch_reps)} items...")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Future -> original_item
            future_to_orig = {executor.submit(normalize_item_llm, ctx_it): orig_it 
                              for orig_it, ctx_it in batch_map.items()}
            
            from concurrent.futures import as_completed
            completed = 0
            for future in as_completed(future_to_orig):
                original_item = future_to_orig[future]
                try:
                    res = future.result()
                    rep_results[original_item] = res
                    completed += 1
                    if completed % 10 == 0 or completed == len(batch_reps):
                        print(f"   - Progress: {completed}/{len(batch_reps)} items completed in current batch")
                except Exception as e:
                    print(f"Error in thread for {original_item}: {e}")
                    rep_results[original_item] = {}
            
            if batch_num < total_batches - 1:
                print(f"Batch {batch_num + 1} completed. {len(rep_results)} items in results map.")
                await asyncio.sleep(0.5)

    # Propagate results back to all original unique items in groups
    for ckey, items in clean_groups.items():
        rep = ckey_to_rep[ckey]
        res = rep_results.get(rep)
        if res:
            for item in items:
                norm_map[item] = res

            
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
        mpack_val = normalize_mpack(get_val(d, ["MPACK", "PACK"]))
        facts_val = get_val(d, ["FACTS", "FACT"])
        
        # 2. CONSTRUCT PRE-GROUP KEY
        # FIX 1: Use ONLY LLM-Standardized Brand (Never trust Excel Brand for grouping)
        llm_brand = str(norm.get("brand", "UNKNOWN")).upper()
        llm_form = str(norm.get("product_form", "UNKNOWN")).upper()
        llm_flavour = str(norm.get("flavour", "UNKNOWN")).upper()
        llm_variant = str(norm.get("variant", "REGULAR")).upper() # Safeguard: Default to REGULAR
        
        if norm.get("confidence", 0) >= LLM_CONFIDENCE_THRESHOLD:
            # HIGH CONFIDENCE: Use LLM Attributes
            
            # FIX 3: ASSORTED Protection (Keep different Assorted names separate)
            assorted_guard = ""
            if llm_form == "ASSORTED":
                # Use a cleaned version of the item name to prevent "TOPMIX" vs "FUNMIX" merging
                assorted_guard = f"|{simple_clean_item(item)}"
            
            is_sf = "SF" if norm.get("is_sugar_free") else "REG"
            # STEP 2 HARD RULE: Family Token Gatekeeper
            llm_line = str(norm.get("product_line", "")).strip().upper()
            
            # 🚨 HARD FAMILY GUARD (MANDATORY)
            # If product_line is missing, downgrade to LOW_CONF to prevent wrong merges
            if not llm_line or llm_line in ["NONE", "UNKNOWN"]:
                # print(f"⚠️  FAMILY MISSING → LOW_CONF :: {item}")
                clean_sig = simple_clean_item(item)
                # KEY CHANGE: Removed facts_val from key
                pre_group_key = (
                    f"LOW_CONF|{llm_brand}|{clean_sig}|"
                    f"{market_val}|{mpack_val}|{norm.get('size', 'UNKNOWN')}"
                )
            else:
                # ✅ ADDED LLM_VARIANT and MPACK to HI_CONF key
                # KEY CHANGE: Removed facts_val from key to consolidate Value and Units metrics
                pre_group_key = (
                    f"HI_CONF|{llm_brand}|{llm_line}|{llm_form}|{llm_flavour}|{llm_variant}|{is_sf}|"
                    f"{market_val}|{mpack_val}|{norm.get('size', 'UNKNOWN')}{assorted_guard}"
                )
        else:
            # FIX 2: Safer LOW_CONF Fallback (Do not blindly merge)
            # We use the cleaned item name as a unique signature to keep questionable items separate
            clean_sig = simple_clean_item(item)
            # KEY CHANGE: Removed facts_val from key
            pre_group_key = (
                f"LOW_CONF|{llm_brand}|{clean_sig}|"
                f"{market_val}|{mpack_val}|{norm.get('size', 'UNKNOWN')}"
            )
        
        pre_groups.setdefault(pre_group_key, []).append(d)

    # ✅ UNIVERSAL FUZZY MERGE STAGE: Merge similar LOW_CONF single items within same (Market+Pack+Facts) context
    # This specifically targets items the AI failed to group, like Kinder or residual Typos.
    
    all_group_keys = list(pre_groups.keys())
    # print(f"Universal Fuzzy Merge Stage: Checking {len(all_group_keys)} groups for residual matches...")
    
    # 1. Group keys by STRICT Context: {Market|Pack|Facts : [keys]}
    context_to_keys = {}
    for k in all_group_keys:
        parts = k.split("|")
        # Identify structure based on HI/LOW flag
        # We only consider LOW_CONF items that are currently SINGLES (len == 1)
        if k.startswith("LOW_CONF|") and len(pre_groups[k]) == 1:
             if len(parts) >= 6:
                 ctx_key = "|".join([parts[3], parts[4], parts[5]]) # Market|Pack|Facts
                 context_to_keys.setdefault(ctx_key, []).append(k)

    # 2. Within each context, merge similar LOW_CONF keys
    merged_count = 0
    for ctx_key, keys in context_to_keys.items():
        if len(keys) < 2: continue
        
        keys.sort()
        merged_this_ctx = set()
        
        for i in range(len(keys)):
            k1 = keys[i]
            if k1 in merged_this_ctx: continue
            if k1 not in pre_groups: continue
            
            for j in range(i + 1, len(keys)):
                k2 = keys[j]
                if k2 in merged_this_ctx: continue
                if k2 not in pre_groups: continue

                # Get items and norms for safety check
                doc1 = pre_groups[k1][0]
                doc2 = pre_groups[k2][0]
                item1 = doc1.get("ITEM", "")
                item2 = doc2.get("ITEM", "")
                
                norm1 = norm_map.get(item1, {})
                norm2 = norm_map.get(item2, {})
                
                # SAFETY LOCK: Even for LOW_CONF, if AI extracted different non-null attributes, respect them
                f1, f2 = norm1.get('flavour'), norm2.get('flavour')
                p1, p2 = norm1.get('product_form'), norm2.get('product_form')
                
                # If flavours exist and are clearly different, do not merge regardless of similarity
                if f1 and f2 and f1 != "UNKNOWN" and f2 != "UNKNOWN" and f1 != f2:
                    continue
                if p1 and p2 and p1 != "UNKNOWN" and p2 != "UNKNOWN" and p1 != p2:
                    continue
                
                # 🚨 STRICT SIZE GUARD: Never merge items with different sizes in Mastering
                s1, s2 = str(norm1.get('size', '')).upper().strip(), str(norm2.get('size', '')).upper().strip()
                if s1 and s2 and s1 not in ["UNKNOWN", "NONE", ""] and s2 not in ["UNKNOWN", "NONE", ""] and s1 != s2:
                    continue

                sig1 = simple_clean_item(item1)
                sig2 = simple_clean_item(item2)
                
                sim = calculate_similarity(sig1, sig2)
                if sim > 0.75:
                     # print(f"      - Comparing LOW_CONF: '{sig1}' vs '{sig2}' | Similarity: {sim:.2f}")
                     pass

                # If fuzzy match > 0.85, merge K2 into K1
                if sim > 0.85:
                    # print(f"   [FUZZY MATCH] Merging LOW_CONF Item '{item2}' INTO '{item1}' (Sim: {sim:.2f})")
                    pre_groups[k1].extend(pre_groups[k2])
                    pre_groups.pop(k2)
                    merged_this_ctx.add(k2)
                    merged_count += 1
    
    if merged_count > 0:
        # print(f"✅ Universal Fuzzy Merge: Merged {merged_count} residual LOW_CONF items.")
        pass
    else:
        # print("ℹ️ Universal Fuzzy Merge: No additional LOW_CONF matches found.")
        pass


    # ✅ REMOVED: Size Tolerance (5g Rules) - Now using exact size in pre_group_key
    final_groups_list = list(pre_groups.values())

    # print(f"Clusters formed after size tolerance: {len(final_groups_list)}")


    
    # ✅ BATCH PROCESSING: Prepare batch operations
    batch_operations = []
    
    # Process Groups
    for cluster_docs in final_groups_list:
        # 🚨 POST-MERGE AUDIT (HARD RULE 2.0)
        # Block if multiple distinct product lines have somehow leaked into the same group
        valid_subgroups = [cluster_docs] # Default is one group
        
        if len(cluster_docs) > 1:
            # 1. FAMILY GUARD (Product Line)
            families_map = {} # fam -> list of docs
            for d in cluster_docs:
                norm = norm_map.get(d.get("ITEM"), {})
                fam = str(norm.get("product_line", "")).strip().upper()
                if not fam or fam in ["NONE", "UNKNOWN"]:
                    fam = f"UNIQUE_{simple_clean_item(d.get('ITEM'))}"
                families_map.setdefault(fam, []).append(d)
            
            if len(families_map) > 1:
                # print(f"⚠️ AUDIT ALERT: Found {len(families_map)} families in one cluster {list(families_map.keys())}. Splitting.")
                valid_subgroups = list(families_map.values())
            else:
                # 2. HARD FLAVOUR & VARIANT GUARDS (Strict Keyword Splitting)
                # Priority-ordered list: MORE SPECIFIC flavours FIRST, generic ones LAST.
                # This prevents "HAZELNUT CHOC CHIP" from being grouped with "DOUBLE CHOC CHIP".
                FLAVOUR_CONFLICTS_PRIORITY = [
                    # Tier 1: Highly specific compound flavours (check first)
                    "SALTED CARAMEL", "DARK CHOCOLATE", "DARK CHOCO", "NUTTY CHOCO",
                    "CHIA SEED", "CHOCOLATE CHIP", "CHOC CHIP", "RED VELVET",
                    # Tier 2: Specific single-ingredient flavours (check before generic CHOCOLATE)
                    "MACADAMIA", "PISTACHIO", "HAZELNUT", "CRANBERRY", "ALMOND",
                    "BLUEBERRY", "STRAWBERRY", "PINEAPPLE", "APPLE", "LEMON",
                    "COCONUT", "PEANUT", "GOJI", "RAISIN", "MATCHA",
                    # Tier 3: Generic flavours (check last)
                    "VANILLA", "SALTED", "CHOCOLATE", "CHEESE", "BUTTER", "ORIGINAL"
                ]
                
                VARIANT_CONFLICTS = [
                    "GOKUBOSO", "MINI", "GIANT", "PREMIUM", "GOLD", "SNOWY"
                    # ✅ REMOVED: "FESTIVE" — Nabati Festive editions are same product (seasonal packaging only)
                ]
                
                # Helper to find which conflict keyword exists in item name
                # Uses PRIORITY ORDER (not length order) to ensure specific flavours win
                def get_conflict_key(name, conflict_list):
                    # 🚨 Use normalized name to catch typos (MACADMIA -> MACADAMIA, HZLNT -> HAZELNUT)
                    name_up = normalize_synonyms(name).upper()
                    # Iterate in PRIORITY ORDER (most specific first)
                    for k in conflict_list:
                        if re.search(rf"\b{re.escape(k)}\b", name_up):
                            return k
                    return None

                flav_groups = {} # key -> docs
                
                for d in cluster_docs:
                    item_name = d.get("ITEM", "")
                    fk = get_conflict_key(item_name, FLAVOUR_CONFLICTS_PRIORITY) or "OTHER_FLAV"
                    vk = get_conflict_key(item_name, VARIANT_CONFLICTS) or "OTHER_VAR"
                    
                    # 🚨 OREO SPECIAL: Treat Original and Vanilla as SAME in Audit to prevent split
                    if "OREO" in item_name.upper() and fk in ["ORIGINAL", "VANILLA"]:
                        fk = "ORIGINAL/VANILLA"
                    
                    # Create a composite key for flavour + variant grouping
                    comp_key = f"{fk}|{vk}"
                    flav_groups.setdefault(comp_key, []).append(d)
                
                if len(flav_groups) > 1:
                    # print(f"⚠️ HARD GUARD: Forced split for {len(flav_groups)} sub-variants in current cluster")
                    valid_subgroups = list(flav_groups.values())

        for group_docs in valid_subgroups:
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
                
                # ✅ FIX: Set BRAND field FIRST before merge_id
                if not doc.get("BRAND"):
                    doc["BRAND"] = norm.get("brand") or "UNKNOWN"
                
                # Store LLM extracted fields (flavour, size are not duplicates)
                doc["flavour"] = norm.get("flavour")
                doc["product_form"] = norm.get("product_form")
                doc["size"] = norm.get("size")
                doc["normalized_item"] = norm.get("base_item")
                doc["llm_confidence_min"] = norm.get("confidence", 0)

                # Generate merge_id AFTER BRAND is set
                doc["merge_id"] = doc.get("merge_id") or f"{doc['BRAND']}_{uuid.uuid4().hex}"

                extend_merge_metadata(
                    base=doc,
                    group_docs=[doc],
                    merge_rule="NO MERGE | SINGLE ITEM",
                    merge_level="NO_MERGE_SINGLE_ITEM"
                )
                
                doc["sheet_name"] = "wersel_match"
                
                # Clean up internal fields
                for k in list(doc.keys()):
                    if k.startswith("_") or k.lower().startswith("unnamed"):
                        doc.pop(k)
                
                # Add to batch operations
                batch_operations.append(UpdateOne(
                    {"merge_id": doc["merge_id"], "sheet_name": doc["sheet_name"]},
                    {"$set": doc},
                    upsert=True
                ))
                continue

            # Merge multiple items
            # 🚀 Main UPC Business Rule: Select record with highest 'MAT Nov'24' as base
            mat_col = next((k for k in group_docs[0] if "mat" in k.lower()), "MAT Nov'24")
            
            def get_mat_val(d):
                try:
                    v = d.get(mat_col, 0)
                    return float(v) if not pd.isna(v) else 0.0
                except: return 0.0

            # Find the record with max MAT stock
            leader_doc = max(group_docs, key=get_mat_val)
            
            # ✅ AUDIT LOG: Show the business logic in action
            print(f"   [Logic] Merging {len(group_docs)} items under Main_UPC: {leader_doc.get('UPC')} ({leader_doc.get('ITEM')[:30]}...) | MAT Stock: {get_mat_val(leader_doc)}")

            base = copy.deepcopy(leader_doc)
            base.pop("_id", None)
            base.pop("_norm", None)
            
            # Sum monthly columns (Prioritizing Sales Value if multiple facts present)
            month_cols = [k for k in base if "w/e" in k.lower() or "mat" in k.lower()]
            
            # Identify if we have Value docs (the preferred metric for summation)
            has_value_docs = any("VALUE" in str(d.get("Facts", d.get("FACTS", ""))).upper() for d in group_docs)
            
            for m in month_cols:
                base[m] = 0.0
            
            for d in group_docs:
                fact_str = str(d.get("Facts", d.get("FACTS", ""))).upper()
                # If we have value docs, only sum value docs to avoid Dollars + Units
                if has_value_docs and "VALUE" not in fact_str:
                    continue
                    
                for m in month_cols:
                    val = d.get(m)
                    try:
                        f_val = float(val)
                        if not math.isnan(f_val):
                            base[m] += f_val
                    except:
                        pass

            # Update Facts field to reflect merging
            if len(set(str(d.get("Facts", d.get("FACTS", ""))) for d in group_docs)) > 1:
                base["Facts"] = "Consolidated (Value Pref)"

            
            # Get norm from first item
            item_name = group_docs[0].get("ITEM")
            norm = norm_map.get(item_name, {})
            
            # ✅ FIX: Set BRAND field FIRST before merge_id
            if not base.get("BRAND"):
                base["BRAND"] = norm.get("brand") or "UNKNOWN"
            
            # Generate merge_id AFTER BRAND is set
            base["merge_id"] = base.get("merge_id") or f"{base['BRAND']}_{uuid.uuid4().hex}"
            
            # Store LLM extracted fields (flavour, variant, size are not duplicates)
            base["flavour"] = norm.get("flavour") or base.get("VARIANT", "") or ""
            base["variant"] = norm.get("variant") or "REGULAR"
            base["product_form"] = norm.get("product_form") or "UNKNOWN"
            base["size"] = norm.get("size") or base.get("NRMSIZE", "")
            base["normalized_item"] = norm.get("base_item") or base.get("ITEM", "")
            base["llm_confidence_min"] = min(norm_map.get(d.get("ITEM"), {}).get("confidence", 0) for d in group_docs)

            extend_merge_metadata(
                base=base,
                group_docs=group_docs,
                merge_rule="BRAND+FLAVOUR+VARIANT+SIZE (LLM) + STRICT KEYS",
                merge_level="MASTER_PRODUCT_MERGE"
            )

            # Add sheet_name for tracking
            base["sheet_name"] = "wersel_match"
            
            # Clean up internal fields (Keep BRAND as it is critical for dashboard)
            redundant_keys = ["VARIANT", "NRMSIZE"] # Removed BRAND from here
            for k in list(base.keys()):
                if k.startswith("_") or k.lower().startswith("unnamed") or k in redundant_keys:
                    base.pop(k)

            # Add to batch operations
            batch_operations.append(UpdateOne(
                {"merge_id": base["merge_id"], "sheet_name": base["sheet_name"]},
                {"$set": base},
                upsert=True
            ))
    
    # ✅ BATCH WRITE: Write in batches of 5000 (5x faster than 1000)
    if batch_operations:
        batch_size = 5000  # Increased from 1000 for faster saves
        total_ops = len(batch_operations)
        
        for i in range(0, total_ops, batch_size):
            # ✅ REMOVED disconnect check here - was causing premature stops
            # Let the save complete even if frontend disconnects
            
            batch = batch_operations[i:i + batch_size]
            # ✅ ULTRA FAST: ordered=False allows parallel execution
            tgt_col.bulk_write(batch, ordered=False)
            print(f"Flow 2: Saved batch: {min(i + batch_size, total_ops)}/{total_ops} master records")
            
            await asyncio.sleep(0)  # Yield for event loop

    
    return {
        "total_processed": len(docs),
        "clusters_created": len(final_groups_list),
        "status": "Success | All items processed and merged according to client rules."
    }
