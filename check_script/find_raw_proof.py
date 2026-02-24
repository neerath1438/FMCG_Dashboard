from pymongo import MongoClient
import os
from dotenv import load_dotenv

def find_raw_proof():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    q = {'Markets': 'Pen Malaysia', 'Facts': 'Sales Value'}
    
    with open('proof_raw.txt', 'w') as f:
        # 1. Null Items (3)
        null_ids = list(db['raw_data'].find({**q, 'ITEM': None}, {"_id": 1}))
        f.write("--- 3 NULL RECORDS (Dropped) ---\n")
        for d in null_ids[:3]:
            f.write(f"db.raw_data.find({{\"_id\": ObjectId(\"{d['_id']}\")}})\n")
            
        # 2. Merged Records (4 merges = 8 raw records)
        merged = list(db['single_stock_data'].find({**q, 'merged_from_docs': {'$gt': 1}}))
        f.write(f"\n--- {len(merged)} MERGED GROUPS (8 total records) ---\n")
        for s_doc in merged:
            upc = s_doc.get('UPC')
            item = s_doc.get('ITEM')
            raw_matches = list(db['raw_data'].find({**q, 'UPC': upc}))
            f.write(f"// Product: {item} (UPC: {upc})\n")
            for r in raw_matches:
                f.write(f"db.raw_data.find({{\"_id\": ObjectId(\"{r['_id']}\")}})\n")
    
    print("Proof saved to proof_raw.txt")

if __name__ == "__main__":
    find_raw_proof()
