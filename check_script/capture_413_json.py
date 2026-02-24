import os
import json
from pymongo import MongoClient
from bson import json_util
from dotenv import load_dotenv

def capture_master_merges():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    q = {'Markets': 'Pen Malaysia', 'Facts': 'Sales Value', 'merged_from_docs': {'$gt': 1}}
    
    # Sort by merged_from_docs descending to show most significant merges first
    merged = list(db['master_stock_data'].find(q).sort('merged_from_docs', -1))
    
    print(f"Captured {len(merged)} merged groups representing the audit gap.")
    
    with open('merged_413.json', 'w') as f:
        f.write(json_util.dumps(merged, indent=2))
    
    print("Saved to merged_413.json")

if __name__ == "__main__":
    capture_master_merges()
