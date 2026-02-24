from pymongo import MongoClient
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

def check_inconsistency(items):
    # Check if a group contains both 'STICK' and 'WAFER' or 'CRISPY' in names
    forms = ["STICK", "WAFER", "CRISPY", "BISCUIT", "COOKIE"]
    found_forms = set()
    for item in items:
        for f in forms:
            if f in item.upper():
                found_forms.add(f)
    return found_forms if len(found_forms) > 1 else None

def run_global_check():
    print("=== GLOBAL MERGING VERIFICATION ===")
    
    # 1. Check for missing product_form
    missing_form = list(master.find({"$or": [{"product_form": None}, {"product_form": "UNKNOWN"}]}))
    print(f"\nItems with missing/unknown product_form: {len(missing_form)}")
    if missing_form:
        brands = {}
        for doc in missing_form:
            b = doc.get("BRAND", "UNKNOWN")
            brands[b] = brands.get(b, 0) + 1
        print("Breakdown by Brand:")
        for b, count in brands.items():
            print(f"  - {b}: {count}")

    # 2. Check for inconsistent merges
    # We look for groups where the item names merged together seem to be different products
    all_merged = list(master.find({"merged_from_docs": {"$gt": 1}}))
    print(f"\nTotal merged master items: {len(all_merged)}")
    
    inconsistent_count = 0
    for doc in all_merged:
        items = doc.get("merge_items", [])
        divergence = check_inconsistency(items)
        if divergence:
            inconsistent_count += 1
            print(f"\nPotential Inconsistent Merge Found!")
            print(f"  Brand: {doc.get('BRAND')}")
            print(f"  Master Item: {doc.get('ITEM')}")
            print(f"  Forms found in names: {divergence}")
            print(f"  UPC: {doc.get('UPC')}")
            print(f"  Names: {items[:5]}...")

    print(f"\nTotal potential inconsistencies found: {inconsistent_count}")
    print("\n=== VERIFICATION END ===")

if __name__ == "__main__":
    run_global_check()
