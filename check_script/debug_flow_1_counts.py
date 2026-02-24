import pandas as pd
import numpy as np
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import re
import math

# Mocking normalize_synonyms if needed (copying from processor.py logically)
def simple_clean_item(name):
    if not name: return ""
    s = str(name).upper()
    for word in ["ITEM", "PACK", "FLAVOUR", "FLV", "BRAND"]:
        s = s.replace(word, " ")
    words = sorted(list(set(re.findall(r'[A-Z0-9]+', s))))
    return "".join(words)

def extract_size_val(size_str):
    if not size_str or str(size_str).strip() == "": return 0.0
    s = str(size_str).upper().replace(" ", "").replace(",", "")
    match = re.search(r'(\d+\.?\d*)', s)
    if match:
        try:
            val = float(match.group(1))
            if 'KG' in s or 'LTR' in s or ('L' in s and 'ML' not in s):
                val *= 1000
            return val
        except: return 0.0
    return 0.0

def debug_flow_1():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    # 7 Items from filtered_7.json
    target_upcs = [40144061, 45183591, 49779059, 50168033, 50168040, 52868788, 54010628]
    
    raw_data_coll = db["raw_data"]
    nielsen_query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
    
    df = pd.DataFrame(list(raw_data_coll.find(nielsen_query)))
    if df.empty:
        print("No raw data found!")
        return

    print(f"Total raw records: {len(df)}")
    
    # Check if targets exist in raw
    found_targets = df[df['UPC'].isin(target_upcs)]
    print(f"Found {len(found_targets)} target items in RAW_DATA")
    
    # Flow 1 logic transitions
    # 1. Null UPC filter
    df_step1 = df[df['UPC'].notnull()].copy()
    print(f"Records after Null UPC filter: {len(df_step1)}")
    
    # 2. Grouping Keys
    # Identify col names (processor.py logic)
    col_map = {c.upper().strip(): c for c in df_step1.columns}
    upc_col = col_map.get("UPC")
    market_col = col_map.get("MARKETS")
    mpack_col = col_map.get("MPACK")
    facts_col = col_map.get("FACTS")
    item_col = col_map.get("ITEM")
    brand_col = col_map.get("BRAND")
    flavour_col = col_map.get("FLAVOUR") or col_map.get("FLAVOR")
    
    fill_val = "UNKNOWN"
    group_keys = [upc_col]
    if market_col: 
        df_step1[market_col] = df_step1[market_col].fillna(fill_val)
        group_keys.append(market_col)
    if mpack_col: 
        df_step1[mpack_col] = df_step1[mpack_col].fillna(fill_val)
        group_keys.append(mpack_col)
    if facts_col: 
        df_step1[facts_col] = df_step1[facts_col].fillna(fill_val)
        group_keys.append(facts_col)
    if item_col:
        df_step1["_group_item_clean"] = df_step1[item_col].apply(simple_clean_item)
        group_keys.append("_group_item_clean")
    if brand_col:
        df_step1[brand_col] = df_step1[brand_col].fillna(fill_val)
        group_keys.append(brand_col)
    if flavour_col:
        df_step1[flavour_col] = df_step1[flavour_col].fillna(fill_val)
        group_keys.append(flavour_col)

    # 3. Create Groups
    groups = df_step1.groupby(group_keys)
    print(f"Total Groups formed: {len(groups)}")
    
    # Check if our targets are in groups
    for upc in target_upcs:
        target_rows = df_step1[df_step1[upc_col] == upc]
        if target_rows.empty:
            print(f"UPC {upc} is MISSING from df_step1")
            continue
            
        # Find which group it belongs to
        keys = target_rows.iloc[0][group_keys].values
        print(f"UPC {upc} Group Key: {keys}")
        
    # Check if any groups have items from our list but merged with others
    single_stock_records = []
    # Simplified bucket logic
    for g_keys, group in groups:
        # Just check count
        single_stock_records.append({"key": g_keys, "count": len(group)})
    
    print(f"Final Single Stock Count: {len(single_stock_records)}")

if __name__ == "__main__":
    debug_flow_1()
