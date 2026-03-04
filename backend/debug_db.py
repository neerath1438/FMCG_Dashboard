
import sys
import os
import pymongo
import json
from bson import json_util

def find_items():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['fmcg_mastering']
    
    output_file = 'd:/git/FMCG_Dashboard/db_debug_output.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        collections = ['raw_data', 'single_stock_data', 'master_stock_data']
        
        for coll_name in collections:
            f.write(f"\n--- Checking Collection: {coll_name} ---\n")
            coll = db[coll_name]
            
            # Search for items that look like Pocky Cookies & Cream 40G
            query = {
                "ITEM": {"$regex": "POCKY", "$options": "i"},
                "$or": [
                    {"ITEM": {"$regex": "40", "$options": "i"}},
                    {"ITEM": {"$regex": "COOKIE", "$options": "i"}}
                ]
            }
            
            items = list(coll.find(query))
            f.write(f"Found {len(items)} items matching query.\n")
            
            # Special check for Master Stock duplicates
            if coll_name == 'master_stock_data':
                cookies_cream_40g = [item for item in items if "40" in item.get("size", "") and ("COOKIE" in str(item.get("flavour", "")).upper() or "CREAM" in str(item.get("flavour", "")).upper())]
                f.write(f"\n--- MASTER STOCK ANALYSIS: Pocky Cookies & Cream 40G ---\n")
                f.write(f"Found {len(cookies_cream_40g)} distinct master records.\n")
                for i, record in enumerate(cookies_cream_40g):
                    f.write(f"\nRecord #{i+1}:\n")
                    f.write(f"  Merge ID: {record.get('merge_id')}\n")
                    f.write(f"  Main Item: {record.get('ITEM')}\n")
                    f.write(f"  Flavour: {record.get('flavour')}\n")
                    f.write(f"  Size: {record.get('size')}\n")
                    f.write(f"  Merged from {record.get('merged_from_docs')} docs\n")
                    f.write(f"  UPCs: {record.get('merged_upcs')}\n")
                    f.write(f"  Items: {record.get('merge_items')}\n")
            
            for item in items:
                item_name = item.get("ITEM", "N/A")
                is_pocky = "POCKY" in item_name.upper()
                is_cookie = "COOKIE" in item_name.upper()
                is_40 = "40" in item_name
                
                # Filter specifically for the target items to keep output manageable but complete
                if is_pocky and (is_cookie or is_40):
                    f.write(f"\nMATCH FOUND in {coll_name}:\n")
                    # Use json_util for MongoDB objects
                    f.write(json_util.dumps(item, indent=2) + "\n")

if __name__ == "__main__":
    find_items()
