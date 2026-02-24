from pymongo import MongoClient
import pandas as pd
import asyncio
from backend.processor import process_excel_flow_1, process_llm_mastering_flow_2
import io
import os

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]

def log(msg, f):
    print(msg)
    f.write(msg + "\n")

async def run_test():
    with open("d:/FMCG_Dashboard/verify_output.txt", "w") as f:
        log("=== NYAM NYAM VERIFICATION START ===", f)
        
        # Identify the correct raw collection
        cols = db.list_collection_names()
        raw_col_name = "raw_data" if "raw_data" in cols else "raw_data_storage"
        log(f"Using collection: {raw_col_name}", f)
        raw_coll = db[raw_col_name]
        
        # Get Nyam Nyam raw data
        nyam_rows = list(raw_coll.find({"ITEM": {"$regex": "NYAM NYAM", "$options": "i"}}))
        if not nyam_rows:
            log("No Nyam Nyam raw data found in 'raw_data' using regex. Trying literal search...", f)
            # Try a broader search just in case
            nyam_rows = list(raw_coll.find({"ITEM": {"$regex": "NYAM", "$options": "i"}}))
            
        if not nyam_rows:
            log("CRITICAL: No Nyam Nyam or NYAM data found in database!", f)
            return

        log(f"Found {len(nyam_rows)} rows for testing.", f)

        # Create a DataFrame
        df = pd.DataFrame(nyam_rows)
        if "_id" in df.columns: df.drop(columns=["_id"], inplace=True)

        # Save to CSV for Flow 1 simulation
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        byte_output = io.BytesIO(output.getvalue().encode('utf-8'))

        log(f"Running Flow 1 for Nyam Nyam rows...", f)
        await process_excel_flow_1(byte_output)
        
        log("\n--- Flow 1 completed. Checking single_stock_data ---", f)
        single = db["single_stock_data"]
        items = list(single.find({"ITEM": {"$regex": "NYAM NYAM", "$options": "i"}}))
        log(f"Found {len(items)} master lines in Flow 1 output.", f)
        for it in items:
            merge_list = it.get('merge_items', [])
            log(f"  - ITEM: {it.get('ITEM')} | UPC: {it.get('UPC')} | MERGED_COUNT: {len(merge_list)}", f)

        log("\n--- Running Flow 2 for Nyam Nyam ---", f)
        # Clear cache for these items first to force fresh LLM evaluation
        cache_coll = db["LLM_CACHE_STORAGE"]
        cache_coll.delete_many({"item": {"$regex": "NYAM", "$options": "i"}})
        
        await process_llm_mastering_flow_2("wersel_match")
        
        log("\n--- Flow 2 completed. Checking master_stock_data ---", f)
        master = db["master_stock_data"]
        final_items = list(master.find({"ITEM": {"$regex": "NYAM NYAM", "$options": "i"}}))
        log(f"Found {len(final_items)} final master items.", f)
        for fit in final_items:
             log(f"  - MASTER: {fit.get('ITEM')} | FORM: {fit.get('product_form')} | MERGED: {len(fit.get('merge_items', []))} docs", f)
             log(f"    - First few merged items: {fit.get('merge_items', [])[:3]}...", f)
        
        log("\n=== NYAM NYAM VERIFICATION END ===", f)

if __name__ == "__main__":
    # Ensure backend is in path
    import sys
    sys.path.append(os.getcwd())
    asyncio.run(run_test())
