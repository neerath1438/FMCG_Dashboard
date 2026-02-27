
import sys
import os
import json
import re
from pymongo import MongoClient

# Add the project root to sys.path so 'backend.database' can be resolved
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Check if we can import
try:
    from backend import processor
except ImportError:
    # Fallback if the path is different
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import processor

def debug_mastering():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    # Items mentioned by user
    search_items = [
        'X1 OREO WAFER ROLL 468G',
        'X1 OREO WAFER ROLL LIM EDT 468G',
        'X1 OREO MINI ORIGINAL 20.4GM',
        'X1 MINI OREO VANILLA 20.4G (POUCH)',
        'X1 OREO RED VELVET 123.5G'
    ]
    
    # Try searching in single_stock_data
    results = list(db['single_stock_data'].find({"ITEM": {"$in": search_items}}))
    if not results:
        print("No items found in single_stock_data matching the search list.")
        # Try a broader search
        results = list(db['single_stock_data'].find({"ITEM": {"$regex": "OREO", "$options": "i"}}))
        print(f"Found {len(results)} total OREO items in single_stock_data.")
    
    print("\n--- ATTRIBUTE ANALYSIS ---")
    for r in results:
        item = r.get("ITEM")
        mpack = processor.normalize_mpack(r.get("MPACK", "X1"))
        
        print(f"\nITEM: {item}")
        print(f"RAW MPACK: {r.get('MPACK')} -> NORM: {mpack}")
        
    # Check master_stock_data for these items
    print("\n--- MASTER_STOCK_DATA RESULTS ---")
    for item_name in search_items:
        master = db['master_stock_data'].find_one({"ITEM": item_name})
        if not master:
            # Search in merge_items array
            master = db['master_stock_data'].find_one({"merge_items": item_name})
            
        if master:
            print(f"ITEM: {item_name}")
            print(f"  Parent ITEM: {master.get('ITEM')}")
            print(f"  Merge ID: {master.get('merge_id')}")
            print(f"  Brand: {master.get('BRAND')}")
            print(f"  Line: {master.get('product_line')}")
            print(f"  Form: {master.get('product_form')}")
            print(f"  Flavour: {master.get('flavour')}")
            print(f"  Variant: {master.get('variant')}")
            print(f"  Size: {master.get('size')}")
        else:
            print(f"ITEM: {item_name} - NOT FOUND in master_stock_data")

if __name__ == "__main__":
    debug_mastering()
