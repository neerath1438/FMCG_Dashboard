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

def debug_final_count():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    nielsen_query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
    nielsen_docs = list(db["master_stock_data"].find(nielsen_query))
    df_nielsen = pd.DataFrame(nielsen_docs)
    
    # Cleaning as in script
    group_cols = ['BRAND', 'ITEM', 'VARIANT', 'MPACK', 'NRMSIZE', 'UPC']
    for col in df_nielsen.columns:
        if col in group_cols or df_nielsen[col].dtype == 'object':
            df_nielsen[col] = df_nielsen[col].fillna("NONE").astype(str).str.strip().str.upper()
    
    df_nielsen['normalized_size'] = df_nielsen['NRMSIZE'].apply(normalize_to_val)
    
    processed_indices = set()
    results_count = 0
    total_df = len(df_nielsen)
    
    for idx, row in df_nielsen.iterrows():
        if idx in processed_indices:
            continue
            
        brand, item, variant, mpack = row['BRAND'], row['ITEM'], row['VARIANT'], row['MPACK']
        size_val = row['normalized_size']
        
        group_mask = (
            (df_nielsen['BRAND'] == brand) &
            (df_nielsen['ITEM'] == item) &
            (df_nielsen['VARIANT'] == variant) &
            (df_nielsen['MPACK'] == mpack)
        )
        
        group_df = df_nielsen[group_mask].copy()
        if size_val is not None:
            group_df = group_df[group_df['normalized_size'].apply(lambda x: abs(x - size_val) <= 5 if x is not None else False)]
        
        group_len = len(group_df)
        if group_len == 0:
            # THIS IS IT! If group_len is 0, we lose the current row!
            # Let's see why it would be 0.
            # Only if df_nielsen[group_mask] doesn't include idx!
            # But idx satisfies group_mask by definition.
            # So maybe df_nielsen[group_mask] is NOT empty, but the size filter drops everything?
            # But the size filter includes 'size_val', which is from 'row'.
            # So 'row' MUST pass the size filter!
            # (abs(size_val - size_val) <= 5 is 0 <= 5 which is True).
            pass

        for g_idx in group_df.index:
            processed_indices.add(g_idx)
            
        results_count += group_len
    
    print(f"NIELSEN_TOTAL: {total_df}")
    print(f"PROCESSED_INDICES: {len(processed_indices)}")
    print(f"RESULTS_COUNT: {results_count}")

if __name__ == "__main__":
    debug_final_count()
