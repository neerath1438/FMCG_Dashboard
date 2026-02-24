import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

def validate_roshini_samples_v3():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # 1. Read input Excel from Roshini
    input_file = r"d:\FMCG_Dashboard\biscuit_uniqueUPC-ITEM_100.xlsx"
    df_roshini = pd.read_excel(input_file, sheet_name="100")
    
    # Standardize column names
    df_roshini.columns = [str(c).upper().strip() for c in df_roshini.columns]
    
    validation_results = []
    
    print(f"Validating {len(df_roshini)} samples from file...")
    
    for idx, row in df_roshini.iterrows():
        upc = str(row.get('UPC')).split('.')[0].strip() # Handle numeric UPCs
        roshini_name = str(row.get('ITEM'))
        
        # A. Check Merging Status
        master_doc = db["master_stock_data"].find_one({"merged_upcs": upc})
        
        # B. Check Gap Analysis Status
        # The gap analysis results are stored in 7eleven_extra_items
        gap_doc = db["7eleven_extra_items"].find_one({"UPC": upc})
        
        # C. Get Raw Details for reference
        raw_doc = db["raw_data"].find_one({"UPC": upc}, {"ITEM": 1, "BRAND": 1})
        
        res = {
            "ROSHINI_UPC": upc,
            "ROSHINI_ITEM_NAME": roshini_name,
            "MATCHED_IN_DB": "YES" if raw_doc or master_doc else "NO",
            "OUR_DATABASE_ITEM": raw_doc.get("ITEM") if raw_doc else "NOT FOUND",
            "MASTER_GROUP_NAME": master_doc.get("ITEM") if master_doc else "NONE",
            "MERGE_RULE": master_doc.get("merge_rule") if master_doc else "NONE",
            "MATCH_LEVEL_IN_7E": gap_doc.get("Match_Level") if gap_doc else "NONE",
            "ARTICLE_DESCRIPTION_7E": gap_doc.get("Article_Description") if gap_doc else "NOT CARRIED"
        }
        
        validation_results.append(res)
    
    # Create Final Report
    df_out = pd.DataFrame(validation_results)
    output_path = r"D:\master_final_data\Roshini_99_Samples_Final_Validation.xlsx"
    df_out.to_excel(output_path, index=False)
    
    print(f"✅ Full validation complete. Results saved to {output_path}")
    
    # Check HWA TAI specifically
    hwa_tai_upc = "200068486668"
    print(f"\n--- Investigating HWA TAI ({hwa_tai_upc}) ---")
    hwa_in_7e = db["7-eleven_data"].count_documents({"ArticleDescription": {"$regex": "HWA TAI", "$options": "i"}})
    print(f"HWA TAI count in 7-Eleven database: {hwa_in_7e}")
    
    if hwa_in_7e == 0:
        print("Reason for NO L2 Match: The Brand 'HWA TAI' does not exist in the 7-Eleven data provided.")
    
    client.close()

if __name__ == "__main__":
    validate_roshini_samples_v3()
