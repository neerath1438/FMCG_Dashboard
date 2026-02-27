
import sys
import os
import asyncio
from pymongo import MongoClient

# Add the project root to sys.path so 'backend.database' can be resolved
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Try importing processor from backend
try:
    from backend import processor
    from backend.database import MASTER_STOCK_COL, get_collection
except ImportError:
    # Fallback: if running from backend folder
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import processor
    from database import MASTER_STOCK_COL, get_collection

async def run_mastering():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    # CLEAR PREVIOUS RESULTS
    print(f"Clearing {MASTER_STOCK_COL}...")
    db[MASTER_STOCK_COL].delete_many({})
    
    # 1. Fetch data from single_stock_data
    docs = list(db['single_stock_data'].find({}))
    print(f"Loaded {len(docs)} items from single_stock_data.")
    
    if not docs:
        print("No items found in single_stock_data. Checking raw_data...")
        docs = list(db['raw_data'].find({}))
        print(f"Loaded {len(docs)} items from raw_data.")
        
    if not docs:
        print("Error: No data found to process.")
        return

    # 2. Run Flow 2 (Mastering)
    print("Starting Mastering process (Flow 2)...")
    result = await processor.process_llm_mastering_flow_2(docs)
    
    print("\n--- RESULTS ---")
    print(result)
    
    # 3. Verify specific Oreo merges
    print("\n--- VERIFICATION OF OREO MERGES ---")
    # Using regex to find the parents
    patterns = [
        ('WAFER ROLL 468G', 'OREO.*WAFER.*ROLL.*468'),
        ('MINI OREO 20.4G', 'OREO.*MINI.*20.4'),
        ('RED VELVET 123.5G', 'OREO.*RED.*VELVET.*123.5')
    ]
    for label, p in patterns:
        print(f"\nChecking Pattern: {label}")
        master_list = list(db['master_stock_data'].find({"ITEM": {"$regex": p, "$options": "i"}}))
        if master_list:
            for master in master_list:
                merge_count_names = len(master.get("merge_items", []))
                merged_docs = master.get("merged_from_docs", 0)
                print(f"   Parent ITEM: '{master.get('ITEM')}'")
                print(f"   Unique Names Merged: {merge_count_names}")
                print(f"   Total Docs Merged: {merged_docs}")
                print(f"   Key: {master.get('merge_id')}")
                for m_item in master.get("merge_items", []):
                    print(f"      - {m_item}")
        else:
            print(f"   NO MASTER RECORD FOUND for this pattern.")

if __name__ == "__main__":
    asyncio.run(run_mastering())
