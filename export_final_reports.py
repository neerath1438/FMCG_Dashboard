import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from export_merging_breakdown import export_merging_breakdown

def export_reports():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # Target directory
    target_dir = r"D:\master_final_data"
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
            print(f"Created directory: {target_dir}")
        except Exception as e:
            print(f"Warning: Could not create directory {target_dir}. Saving to current directory. Error: {e}")
            target_dir = "."

    def standardize_and_order_master(df):
        """Helper to enforce strict order, renaming, and uppercase headers for Master Data"""
        
        # 0. Initial column mapping for clarity (AI vs Raw)
        rename_map = {
            'variant': 'AI_VARIANT',
            'flavour': 'AI_FLAVOUR',
            'size': 'AI_SIZE',
            'product_form': 'AI_FORM',
            'VARIANT': 'RAW_VARIANT',
            'NRMSIZE': 'RAW_SIZE'
        }
        
        # Rename if they exist (case-sensitive at first)
        df = df.rename(columns=rename_map)

        # 1. Uppercase all headers (after renaming)
        df.columns = [str(c).upper() for c in df.columns]
        cols = df.columns.tolist()

        # 2. Identify and sort monthly columns chronologically
        month_order = {
            'DEC 23': 1, 'JAN 24': 2, 'FEB 24': 3, 'MAR 24': 4, 'APR 24': 5, 
            'MAY 24': 6, 'JUN 24': 7, 'JUL 24': 8, 'AUG 24': 9, 'SEP 24': 10, 
            'OCT 24': 11, 'NOV 24': 12
        }
        
        month_cols = []
        for c in cols:
            # Match pattern like "APR 24 - W/E 30/04/24"
            parts = c.split(" - ")
            if len(parts) > 1 and parts[0] in month_order:
                month_cols.append((c, month_order[parts[0]]))
        
        # Sort month columns by their numeric value
        month_cols.sort(key=lambda x: x[1])
        sorted_month_names = [x[0] for x in month_cols]

        # 3. Define the strict groups for sorting (using New Names)
        identity_cols = [
            'UPC', 'BRAND', 'ITEM', 'AI_FLAVOUR', 'AI_FORM', 'AI_SIZE', 
            'AI_VARIANT', 'NORMALIZED_ITEM', 'MERGE_ID', 'SHEET_NAME'
        ]
        attribute_cols = [
            'FACTS', 'MANUFACTURER', 'MPACK', 'MARKETS', 'RAW_SIZE', 
            'PRODUCT SEGMENT', 'RAW_VARIANT', 'VARIANT2'
        ]
        analytical_cols = ["MAT NOV'24"]
        audit_cols = [
            'LLM_CONFIDENCE_MIN', 'MERGE_ITEMS', 'MERGE_LEVEL', 
            'MERGE_RULE', 'MERGED_FROM_DOCS', 'MERGED_UPCS'
        ]

        # 4. Filter existing columns in each group
        final_order = []
        for group in [identity_cols, attribute_cols, sorted_month_names, analytical_cols, audit_cols]:
            final_order.extend([c for c in group if c in cols])
        
        # Add any stray columns left over
        remaining = [c for c in cols if c not in final_order]
        return df[final_order + remaining]

    # 1. Export Master Stock Enriched Data
    print("Exporting Master Stock Enriched Data...")
    master_docs = list(db["master_stock_data"].find({}, {"_id": 0}))
    if master_docs:
        df_master = pd.DataFrame(master_docs)
        df_master = standardize_and_order_master(df_master)
        
        path = os.path.join(target_dir, "Master_Stock_Enriched_v2.xlsx")
        df_master.to_excel(path, index=False)
        print(f"✅ Exported {len(df_master)} records to {path}")
    else:
        print("⚠️ master_stock_data collection is empty.")

    # 2. Export 7-Eleven Gap Analysis (Carried + Not Carried)
    print("Exporting 7-Eleven Gaps/Carried Data...")
    gap_docs = list(db["7eleven_extra_items"].find({}, {"_id": 0}))
    if gap_docs:
        df_gap = pd.DataFrame(gap_docs)
        
        # Rename for gap report to match Master (if attributes present)
        df_gap = df_gap.rename(columns={'variant': 'AI_VARIANT', 'flavour': 'AI_FLAVOUR'})
        df_gap.columns = [str(c).upper() for c in df_gap.columns] # UPPERCASE
        
        # Preferred order for gap report (Using new names)
        gap_pref = ["UPC", "ITEM", "MAIN_UPC", "UPC_GROUPNAME", "ARTICLECODE", "GTIN", "ARTICLE_DESCRIPTION", "AI_FLAVOUR", "AI_VARIANT"]
        existing_gap = [c for c in gap_pref if c in df_gap.columns]
        rem_gap = [c for c in df_gap.columns if c not in existing_gap]
        df_gap = df_gap[existing_gap + rem_gap]

        # Export variants
        path_all = os.path.join(target_dir, "7Eleven_Gap_Analysis_v2.xlsx")
        df_gap.to_excel(path_all, index=False)
        
        df_not = df_gap[df_gap['ARTICLECODE'] == 'NONE'].copy()
        if not df_not.empty:
            df_not.to_excel(os.path.join(target_dir, "7Eleven_Not_Carried_Items_v2.xlsx"), index=False)
        
        df_car = df_gap[df_gap['ARTICLECODE'] != 'NONE'].copy()
        if not df_car.empty:
            df_car.to_excel(os.path.join(target_dir, "7Eleven_Carried_Items_v2.xlsx"), index=False)
        print(f"✅ Exported Gap Analysis suite to {target_dir}")
    else:
        print("⚠️ 7eleven_extra_items collection is empty.")

    # 3. Raw Data Exports
    for col_name, file_name in [("raw_data", "Nielsen_Raw_Data_Full_v2.xlsx"), ("7-eleven_data", "Seven_Eleven_Data_Full_v2.xlsx")]:
        docs = list(db[col_name].find({}, {"_id": 0}))
        if docs:
            df_raw = pd.DataFrame(docs)
            df_raw.columns = [str(c).upper() for c in df_raw.columns]
            df_raw.to_excel(os.path.join(target_dir, file_name), index=False)
            print(f"✅ Exported {col_name} to {file_name}")

    # 4. Nielsen Merging Breakdown (Detailed Audit)
    print("Exporting Nielsen Merging Breakdown (v3)...")
    export_merging_breakdown()

    client.close()

if __name__ == "__main__":
    export_reports()
