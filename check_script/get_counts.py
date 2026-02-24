from pymongo import MongoClient
import os
import pandas as pd
from dotenv import load_dotenv
import re

def normalize_to_val(size_str):
    if not size_str or size_str == 'NONE': return None
    size_str = str(size_str).upper()
    match = re.search(r'(\d+\.?\d*)\s*(G|KG|ML|L)', size_str)
    if not match:
        match = re.search(r'(\d+\.?\d*)', size_str)
        if match: return float(match.group(1))
        return None
    val = float(match.group(1))
    unit = match.group(2)
    if unit in ['KG', 'L']: return val * 1000
    return val

def get_report_counts():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    # 1. Nielsen Filtered Data
    query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
    nielsen_docs = list(db["master_stock_data"].find(query))
    total_nielsen = len(nielsen_docs)
    
    # Simulate Grouping to get Master Count
    df = pd.DataFrame(nielsen_docs)
    df['normalized_size'] = df['NRMSIZE'].apply(normalize_to_val)
    
    groups_count = 0
    processed = set()
    for idx, row in df.iterrows():
        if idx in processed: continue
        brand, item, variant, mpack = row['BRAND'], row['ITEM'], row['VARIANT'], row['MPACK']
        size = row['normalized_size']
        
        mask = (df['BRAND'] == brand) & (df['ITEM'] == item) & (df['VARIANT'] == variant) & (df['MPACK'] == mpack)
        group_df = df[mask].copy()
        if size is not None:
            group_df = group_df[group_df['normalized_size'].apply(lambda x: abs(x - size) <= 5 if x is not None else False)]
        
        for g_idx in group_df.index: processed.add(g_idx)
        groups_count += 1

    # 2. 7-Eleven Data
    seven_total = db['7-eleven_data'].count_documents({})
    seven_unique_gtin = len(db['7-eleven_data'].distinct("GTIN"))
    
    # 3. Final Results
    final_total = db['7eleven_extra_items'].count_documents({})
    matched = db['7eleven_extra_items'].count_documents({"Article_Description": {"$ne": "NOT CARRIED"}})
    gaps = db['7eleven_extra_items'].count_documents({"Article_Description": "NOT CARRIED"})
    
    print(f"NIELSEN_TOTAL|{total_nielsen}")
    print(f"NIELSEN_GROUPS|{groups_count}")
    print(f"7E_TOTAL|{seven_total}")
    print(f"7E_UNIQUE_GTIN|{seven_unique_gtin}")
    print(f"FINAL_TOTAL|{final_total}")
    print(f"MATCHED|{matched}")
    print(f"GAPS|{gaps}")

if __name__ == "__main__":
    get_report_counts()
