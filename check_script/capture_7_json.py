import os
import json
from pymongo import MongoClient
from bson import json_util
from dotenv import load_dotenv

def get_full_missing_json():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    q = {'Markets': 'Pen Malaysia', 'Facts': 'Sales Value'}
    
    raw_docs = list(db['raw_data'].find(q))
    single_docs = list(db['single_stock_data'].find(q))
    
    single_ids = set(doc['_id'] for doc in single_docs)
    missing = [doc for doc in raw_docs if doc['_id'] not in single_ids]
    
    print(f"Total Missing found: {len(missing)}")
    
    with open('filtered_7.json', 'w') as f:
        f.write(json_util.dumps(missing[:7], indent=2))
    
    print("Saved to filtered_7.json")

if __name__ == "__main__":
    get_full_missing_json()
