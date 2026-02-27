
from pymongo import MongoClient
import re

def debug_nabati_merges():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    search_patterns = [
        ('RICHEESE', 'RICHEESE.*145'),
        ('NEXTAR STRAWBERRY', 'NEXTAR.*STRAWBERRY.*106'),
        ('NEXTAR BROWNIES', 'NEXTAR.*BROWNIES.*272')
    ]
    
    print("=== SINGLE_STOCK_DATA CHECK ===")
    for label, pattern in search_patterns:
        print(f"\nChecking Single Stock: {label}")
        docs = list(db['single_stock_data'].find({'ITEM': {'$regex': pattern, '$options': 'i'}}))
        for d in docs:
            print(f" - {d.get('ITEM')} | Brand: {d.get('BRAND')} | UPC: {d.get('UPC')}")

    print("\n=== MASTER_STOCK_DATA CHECK ===")
    for label, pattern in search_patterns:
        print(f"\nChecking Master Stock: {label}")
        masters = list(db['master_stock_data'].find({
            '$or': [
                {'ITEM': {'$regex': pattern, '$options': 'i'}},
                {'merge_items': {'$regex': pattern, '$options': 'i'}}
            ]
        }))
        for m in masters:
            print(f" PARENT: {m.get('ITEM')}")
            print(f"  - Merged Items: {m.get('merge_items')}")
            print(f"  - Attributes: Brand={m.get('BRAND')}, Line={m.get('product_line')}, Flavour={m.get('flavour')}, Size={m.get('size')}")
            print(f"  - Docs Count: {m.get('merged_from_docs')}")

if __name__ == "__main__":
    debug_nabati_merges()
