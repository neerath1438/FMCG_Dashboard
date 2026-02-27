
from pymongo import MongoClient

def search_oreo():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    search_terms = ['OREO MINI ORIGINAL 20.4GM', 'MINI OREO VANILLA 20.4G', '20.4']
    
    print("=== SEARCHING SINGLE_STOCK_DATA ===")
    for term in search_terms:
        print(f"\nSearching for: {term}")
        results = list(db['single_stock_data'].find({'ITEM': {'$regex': term, '$options': 'i'}}))
        for r in results:
            print(f" - {r['ITEM']}")

    print("\n=== SEARCHING MASTER_STOCK_DATA ===")
    for term in search_terms:
        print(f"\nSearching for: {term}")
        # Search as parent
        results = list(db['master_stock_data'].find({'ITEM': {'$regex': term, '$options': 'i'}}))
        for r in results:
            print(f" [PARENT] {r['ITEM']} | Children: {r.get('merge_items')}")
        
        # Search as child
        results = list(db['master_stock_data'].find({'merge_items': {'$regex': term, '$options': 'i'}}))
        for r in results:
            print(f" [AS CHILD] {term} found in Parent: {r['ITEM']} | Full Merged List: {r.get('merge_items')}")

if __name__ == "__main__":
    search_oreo()
