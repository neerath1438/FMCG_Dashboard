import os
from pymongo import MongoClient
from dotenv import load_dotenv

def investigate_discrepancy():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    q = {'Markets': 'Pen Malaysia', 'Facts': 'Sales Value'}
    
    # Get all raw IDs
    raw_docs = list(db['raw_data'].find(q))
    raw_total = len(raw_docs)
    
    # Get all single stock IDs
    single_docs = list(db['single_stock_data'].find(q))
    single_total = len(single_docs)
    
    print(f"Raw Total: {raw_total}")
    print(f"Single Total: {single_total}")
    print(f"Difference: {raw_total - single_total}")
    
    single_ids = set(doc['_id'] for doc in single_docs)
    
    missing = [doc for doc in raw_docs if doc['_id'] not in single_ids]
    
    print("\n--- Detailed View of Filtered Items ---")
    for doc in missing:
        print(f"ID: {doc['_id']}")
        print(f"ITEM: {repr(doc.get('ITEM'))}")
        print(f"UPC: {repr(doc.get('UPC'))}")
        print(f"BRAND: {repr(doc.get('BRAND'))}")
        print(f"NRMSIZE: {repr(doc.get('NRMSIZE'))}")
        print("-" * 30)

if __name__ == "__main__":
    investigate_discrepancy()
