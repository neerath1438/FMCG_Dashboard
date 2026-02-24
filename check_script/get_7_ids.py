from pymongo import MongoClient
import os
from dotenv import load_dotenv

def get_proof_ids():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    q = {'Markets': 'Pen Malaysia', 'Facts': 'Sales Value'}
    
    # 1. Find the 3 Null records
    null_docs = list(db['raw_data'].find({**q, 'ITEM': None}))
    with open('proof_ids.txt', 'w') as f:
        f.write("--- 3 NULL RECORDS (Dropped) ---\n")
        for d in null_docs[:3]:
            f.write(f"db.raw_data.find({{\"_id\": ObjectId(\"{d['_id']}\")}})\n")

        # 2. Find the Merged records
        merged_in_single = list(db['single_stock_data'].find({**q, 'merged_from_docs': {'$gt': 1}}))
        
        f.write("\n--- 4 MERGED RECORDS (Duplicates) ---\n")
        if not merged_in_single:
            f.write("// No records with merged_from_docs > 1 found in single_stock_data for this market/fact.\n")
            # Fallback: Just look for any duplicates in raw data
            raw_all = list(db['raw_data'].find(q))
            from collections import Counter
            upc_item_list = [(str(d.get('UPC')), str(d.get('ITEM')), str(d.get('NRMSIZE'))) for d in raw_all if d.get('ITEM') is not None]
            counts = Counter(upc_item_list)
            for key, count in counts.items():
                if count > 1:
                    f.write(f"// Raw Duplicate Found: {key} (Count: {count})\n")
                    matches = [d for d in raw_all if (str(d.get('UPC')), str(d.get('ITEM')), str(d.get('NRMSIZE'))) == key]
                    for r in matches:
                        f.write(f"db.raw_data.find({{\"_id\": ObjectId(\"{r['_id']}\")}})\n")
        else:
            for s_doc in merged_in_single:
                item = s_doc.get('ITEM')
                upc = s_doc.get('UPC')
                # Flexible query
                raw_matches = list(db['raw_data'].find({
                    **q, 
                    '$or': [{'UPC': upc}, {'UPC': str(upc)}],
                    'ITEM': item
                }))
                f.write(f"// Product: {item} (UPC: {upc}) found {len(raw_matches)} times in Raw:\n")
                for r in raw_matches:
                    f.write(f"db.raw_data.find({{\"_id\": ObjectId(\"{r['_id']}\")}})\n")
    
    print("IDs saved to proof_ids.txt")

if __name__ == "__main__":
    get_proof_ids()
