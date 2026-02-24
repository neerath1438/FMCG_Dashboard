from pymongo import MongoClient
import os
from dotenv import load_dotenv

def find_exact_7():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    q = {'Markets': 'Pen Malaysia', 'Facts': 'Sales Value'}
    
    with open('exact_7_ids.txt', 'w') as f:
        f.write("=== EXACT MONGO QUERIES FOR 7-RECORD GAP PROOF ===\n\n")
        
        # 1. THE 3 DROPPED RECORDS (ITEM: null)
        f.write("--- CATEGORY 1: DROPPED (3 Records) ---\n")
        nulls = list(db['raw_data'].find({**q, 'ITEM': None}))
        for d in nulls[:3]:
            f.write(f"db.raw_data.find({{\"_id\": ObjectId(\"{d['_id']}\")}})\n")
            
        # 2. THE 4 MERGED REDUCTIONS (8 Records in Raw -> 4 Records in Single)
        f.write("\n--- CATEGORY 2: MERGED REDUCTIONS (4 Records Gap) ---\n")
        merged = list(db['single_stock_data'].find({**q, 'merged_from_docs': {'$gt': 1}}))
        
        for s_doc in merged:
            upc = s_doc.get('UPC')
            item = s_doc.get('ITEM')
            # The raw docs that formed this single doc
            raw_matches = list(db['raw_data'].find({**q, 'UPC': upc}))
            
            f.write(f"// Product: {item} (UPC: {upc}) | Raw Count: {len(raw_matches)} -> Merged to 1\n")
            for r in raw_matches:
                f.write(f"db.raw_data.find({{\"_id\": ObjectId(\"{r['_id']}\")}})\n")
                
    print("Exact IDs saved to exact_7_ids.txt")

if __name__ == "__main__":
    find_exact_7()
