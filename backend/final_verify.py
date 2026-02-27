
from pymongo import MongoClient

def verify_merges():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    patterns = ['OREO.*WAFER.*ROLL.*468', 'OREO.*MINI', 'RED VELVET.*123.5']
    
    print("--- OREO MERGE VERIFICATION ---")
    for p in patterns:
        print(f"\nPattern: {p}")
        masters = list(db['master_stock_data'].find({"ITEM": {"$regex": p, "$options": "i"}}))
        if not masters:
            # Check if they are children
            parent = db['master_stock_data'].find_one({"merge_items": {"$regex": p, "$options": "i"}})
            if parent:
                print(f"  Merged under parent: {parent.get('ITEM')}")
            else:
                print("  No record found.")
            continue
            
        for m in masters:
            print(f"  PARENT: {m.get('ITEM')}")
            print(f"  Merged Names: {m.get('merge_items')}")
            print(f"  Total Docs: {m.get('merged_from_docs')}")
            print(f"  Attributes: Line={m.get('product_line')}, Flavour={m.get('flavour')}, Size={m.get('size')}")

if __name__ == "__main__":
    verify_merges()
