from pymongo import MongoClient
import pandas as pd
import os

def export_qa_report():
    print("🚀 Connecting to MongoDB...")
    client = MongoClient("mongodb://localhost:27017/")
    db = client["fmcg_mastering"]
    master_coll = db["master_stock_data"]

    # --- QUERY 1: Non-Merged Items (Single items) ---
    non_merged_query = {
        "Facts": "Sales Value",
        "$or": [
            { "merge_items": { "$exists": False } },
            { "merge_items": { "$size": 1 } }
        ]
    }
    
    # --- QUERY 2: Merged Items (Multiple source documents) ---
    # We use > 1 to specifically get the actual merges for QA
    merged_query = { 
        "Facts": "Sales Value",
        "$expr": { "$gt": [{ "$size": "$merge_items" }, 1] } 
    }

    output_file = "qa_verification_report.xlsx"
    print(f"🔍 Fetching data for {output_file}...")

    # Fetch data
    merged_data = list(master_coll.find(merged_query, {"_id": 0}))
    non_merged_data = list(master_coll.find(non_merged_query, {"_id": 0}))

    print(f"📊 Merged Items found: {len(merged_data)}")
    print(f"📊 Non-Merged Items found: {len(non_merged_data)}")

    def clean_for_excel(data_list):
        if not data_list: return []
        cleaned = []
        for doc in data_list:
            clean_doc = {}
            for k, v in doc.items():
                if isinstance(v, list):
                    clean_doc[k] = " | ".join(map(str, v))
                else:
                    clean_doc[k] = v
            cleaned.append(clean_doc)
        return cleaned

    print("📄 Creating Excel file with two sheets...")
    
    # Create DataFrames
    df_merged = pd.DataFrame(clean_for_excel(merged_data))
    df_non_merged = pd.DataFrame(clean_for_excel(non_merged_data))

    # Write to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        if not df_merged.empty:
            df_merged.to_sheet_name = "Merged Items"
            df_merged.to_excel(writer, sheet_name="Merged Items", index=False)
        
        if not df_non_merged.empty:
            df_non_merged.to_excel(writer, sheet_name="Non-Merged Items", index=False)

    print(f"✨ Success! Report generated: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    export_qa_report()
