from pymongo import MongoClient

def run_audit():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['fmcg_mastering']
    
    query = {
        "Markets": "EM MT Hmkt/Smkt/Mini",
        "Facts": "Sales Value",
        "$expr": { "$gt": [{ "$size": "$merge_items" }, 1] }
    }
    
    items = list(db['master_stock_data'].find(query))
    
    if not items:
        print("No merged items found for this query.")
        return

    print(f"Found {len(items)} merged master records.\n")
    for it in items:
        print("-" * 50)
        print(f"MASTER ITEM: {it.get('ITEM')}")
        print(f"BRAND (Master): {it.get('BRAND')}")
        print(f"FLAVOUR (AI): {it.get('flavour')}")
        print(f"FORM (AI): {it.get('product_form')}")
        print(f"MERGE ITEMS ({len(it.get('merge_items', []))}):")
        for m in it.get('merge_items', []):
            print(f"  - {m}")
        print("-" * 50)

if __name__ == "__main__":
    run_audit()
