import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import re
import sys

# Function to normalize size to grams/ml
def normalize_to_val(size_str):
    if not size_str or size_str == 'NONE':
        return None
    
    size_str = str(size_str).upper()
    
    # Try Regex to get number and unit
    match = re.search(r'(\d+\.?\d*)\s*(G|KG|ML|L)', size_str)
    if not match:
        # Try just number
        match = re.search(r'(\d+\.?\d*)', size_str)
        if match:
            return float(match.group(1))
        return None
    
    val = float(match.group(1))
    unit = match.group(2)
    
    if unit == 'KG' or unit == 'L':
        return val * 1000
    return val

def run_gap_analysis():
    load_dotenv()
    
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # 1. Load Nielsen Data (master_stock_data)
    # Filter: Sales Value, Exclude 7-Eleven markets
    print("Loading Nielsen data from master_stock_data...")
    nielsen_query = {
        "Facts": "Sales Value",
        "Markets": "Pen Malaysia" 
    }
    nielsen_docs = list(db["master_stock_data"].find(nielsen_query))
    print(f"Loaded {len(nielsen_docs)} Nielsen documents.")
    
    # 2. Load 7-Eleven Data
    print("Loading 7-Eleven data...")
    seven_docs = list(db["7-eleven_data"].find())
    print(f"Loaded {len(seven_docs)} 7-Eleven documents.")
    
    if not seven_docs:
        print("7-Eleven data not found. Please run import_7eleven.py first.")
        return

    # Convert to DataFrames
    df_nielsen = pd.DataFrame(nielsen_docs)
    df_7e = pd.DataFrame(seven_docs)
    
    # Standardize Column Names to UPPERCASE and Deduplicate to avoid case-sensitivity and duplicate issues
    df_nielsen.columns = [c.upper() for c in df_nielsen.columns]
    df_nielsen = df_nielsen.loc[:, ~df_nielsen.columns.duplicated()]
    
    df_7e.columns = [c.upper() for c in df_7e.columns]
    df_7e = df_7e.loc[:, ~df_7e.columns.duplicated()]
    
    # Critical Columns for Matching and Grouping (in UPPERCASE)
    group_cols = ['BRAND', 'ITEM', 'VARIANT', 'MPACK', 'NRMSIZE', 'UPC', 'GTIN', 'ARTICLECODE', 'ARTICLEDESCRIPTION', 'L4_DESCRIPTION_BRAND', 'AI_BRAND']
    
    # Clean data (Strip, Upper, and Handle NaNs)
    for df in [df_nielsen, df_7e]:
        for col in df.columns:
            if col in group_cols or df[col].dtype == 'object':
                # Ensure we are dealing with a Series and not a DataFrame
                if isinstance(df[col], pd.Series):
                    df[col] = df[col].fillna("NONE").astype(str).str.strip().str.upper()
                else:
                    # If somehow still a DataFrame, take first column
                    df[col] = df[col].iloc[:, 0].fillna("NONE").astype(str).str.strip().str.upper()

    # --- DEDUPLICATION ---
    # 1. Nielsen Data: Process all records as requested (No deduplication)
    print(f"Total Nielsen records to process: {len(df_nielsen)}")

    # 2. Deduplicate 7-Eleven (GTIN)
    initial_7e = len(df_7e)
    # Keeping first occurrence of GTIN
    df_7e = df_7e.drop_duplicates(subset=['GTIN'])
    print(f"Deduplicated 7-Eleven: {initial_7e} -> {len(df_7e)}")
    # ---------------------

    # 3. Matching Logic
    extra_items = []
    
    # Prepare 7-Eleven data for faster lookup (grouped by Brand)
    seven_by_brand = {}
    for _, row in df_7e.iterrows():
        # Priority: AI_BRAND > L4_DESCRIPTION_BRAND
        brand = str(row.get('AI_BRAND', row.get('L4_DESCRIPTION_BRAND', ''))).upper().strip()
        if brand not in seven_by_brand:
            seven_by_brand[brand] = []
        seven_by_brand[brand].append(row)
        
    print("Performing Grouping and Gap Analysis...")
    
    # 3. Group Nielsen Items
    # Rules: Brand, Item, Variant, MPack exact, Size ±5g
    nielsen_groups = []
    processed_indices = set()
    
    # Pre-calculate normalized sizes for Nielsen
    df_nielsen['NORMALIZED_SIZE'] = df_nielsen['NRMSIZE'].apply(normalize_to_val)
    
    for idx, row in df_nielsen.iterrows():
        if idx in processed_indices:
            continue
            
        # Start a new group
        brand = str(row['BRAND'])
        item = str(row['ITEM'])
        variant = str(row['VARIANT'])
        mpack = str(row['MPACK'])
        size_val = row['NORMALIZED_SIZE']
        
        # Find similar items in the same group
        group_mask = (
            (df_nielsen['BRAND'] == brand) &
            (df_nielsen['ITEM'] == item) &
            (df_nielsen['VARIANT'] == variant) &
            (df_nielsen['MPACK'] == mpack)
        )
        
        group_df = df_nielsen[group_mask].copy()
        # Filter group_df further by size tolerance ±5g
        if pd.notnull(size_val):
            group_df = group_df[group_df['NORMALIZED_SIZE'].apply(lambda x: abs(x - size_val) <= 5 if pd.notnull(x) else False)]
        
        if group_df.empty:
            # Fallback: if group_mask also failed, just take the current row to avoid loss
            group_df = df_nielsen.loc[[idx]].copy()

        # Mark as processed
        for g_idx in group_df.index:
            processed_indices.add(g_idx)
            
        nielsen_groups.append(group_df)
    
    print(f"Formed {len(nielsen_groups)} Nielsen groups.")
    
    results = []
    # 4. Compare Groups against 7-Eleven
    total_groups = len(nielsen_groups)
    for i, group in enumerate(nielsen_groups):
        if group.empty:
            print(f"Warning: Group {i+1} is empty, skipping.")
            continue
            
        if (i + 1) % 100 == 0:
            print(f"Comparing group {i+1}/{total_groups}...")

        # Check if ANY item in group has UPC == GTIN
        group_upcs = set(group['UPC'].astype(str).tolist())
        
        # Prepare defaults
        is_carried = False
        first_row = group.iloc[0]
        main_upc = str(first_row['UPC']) # Temporary default
        article_code = "NONE"
        gtin = "NONE"
        article_desc = "NOT CARRIED"
        match_level = "NONE"
        
        # Check for Level 1 Match (UPC == GTIN)
        l1_match = df_7e[df_7e['GTIN'].astype(str).isin(group_upcs)]
        
        if not l1_match.empty:


            is_carried = True
            # Preference: If UPC == GTIN, use that as Main_UPC
            match_row = l1_match.iloc[0]
            main_upc = str(match_row['GTIN'])
            article_code = str(match_row['ARTICLECODE'])
            gtin = str(match_row['GTIN'])
            article_desc = str(match_row['ARTICLEDESCRIPTION'])
            match_level = "L1 (UPC Match)"
        else:
            # Level 2: Attribute Match
            # 🚀 Main UPC Business Rule: Find record with highest 'MAT Nov'24' in group
            mat_col = next((k for k in group.columns if "MAT NOV'24" in k.upper()), None)
            
            def get_mat_val_gap(r):
                if not mat_col: return 0.0
                try:
                    v = r.get(mat_col, 0)
                    return float(v) if pd.notnull(v) else 0.0
                except: return 0.0

            if not group.empty:
                max_row = group.assign(mat_val=group.apply(get_mat_val_gap, axis=1)).sort_values('mat_val', ascending=False).iloc[0]
                main_upc = str(max_row['UPC'])
            else:
                main_upc = str(group.iloc[0]['UPC']) if not group.empty else "NONE"

            # Check if group attributes match any 7-Eleven item

            variant = str(first_row.get('variant', first_row.get('VARIANT', 'NONE')))
            mpack = str(first_row.get('MPACK', 'X1'))
            size_val = first_row.get('NORMALIZED_SIZE')
            
            p_matches = seven_by_brand.get(brand, [])
            for s_row in p_matches:
                # Compare against extracted 7-Eleven attributes
                s_variant = str(s_row.get('7E_VARIANT'))
                s_mpack = str(s_row.get('7E_MPACK'))
                
                if s_variant == variant and s_mpack == mpack:
                    s_size = normalize_to_val(s_row.get('7E_NRMSIZE'))
                    if pd.notnull(size_val) and pd.notnull(s_size):
                        if abs(size_val - s_size) <= 5:
                            is_carried = True
                            article_code = str(s_row['ARTICLECODE'])
                            gtin = str(s_row['GTIN'])
                            article_desc = str(s_row['ARTICLEDESCRIPTION'])
                            match_level = "L2 (Gemini Attribute Match)"
                            break
        
        # The user wants BOTH matched and unmatched items in the final report.
        for _, n_row in group.iterrows():
            results.append({
                "UPC": str(n_row['UPC']),
                "ITEM": str(n_row['ITEM']),
                "Mapping_ID": str(n_row.get('merge_id', 'NONE')), # Traceability for QA
                "Main_UPC": main_upc,
                "UPC_GroupName": str(n_row.get('NORMALIZED_ITEM', n_row.get('ITEM'))),
                "Brand": str(n_row.get('BRAND')),
                "Variant": variant,
                "MPack": mpack,
                "Size": str(n_row.get('NRMSIZE')),
                "ArticleCode": article_code,
                "GTIN": gtin,
                "Article_Description": article_desc,
                "Match_Level": match_level
            })

    if results:
        print(f"Total items processed for report: {len(results)}. Exporting...")
        df_out = pd.DataFrame(results)
        
        # Ensure column order matches Roshini's request
        final_cols = ["UPC", "ITEM", "Mapping_ID", "Main_UPC", "UPC_GroupName", "Brand", "Variant", "MPack", "Size", "ArticleCode", "GTIN", "Article_Description", "Match_Level"]
        df_out = df_out[final_cols]
        
        output_file = "7eleven_gap_analysis.xlsx"
        df_out.to_excel(output_file, index=False)
        print(f"Exported to {output_file}")
        
        # Insert into MongoDB collection
        results_collection = "7eleven_extra_items"
        print(f"Inserting results into MongoDB collection: {results_collection}...")
        db[results_collection].delete_many({}) # Clear old results
        db[results_collection].insert_many(results)
        print("MongoDB insertion completed.")
    else:
        print("No extra items found (all Nielsen items carried by 7-Eleven).")

if __name__ == "__main__":
    run_gap_analysis()
