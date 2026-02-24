from pymongo import MongoClient
import os
from dotenv import load_dotenv

def analyze_merges():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    q = {'Markets': 'Pen Malaysia', 'Facts': 'Sales Value', 'merged_from_docs': {'$gt': 1}}
    merged = list(db['master_stock_data'].find(q))
    
    print(f"Total Merged Groups: {len(merged)}")
    total_reduction = sum(d.get('merged_from_docs', 1) - 1 for d in merged)
    print(f"Total Record Reduction: {total_reduction}")
    
    print("\nSample Merges:")
    for d in merged[:10]:
        print(f"ITEM: {d.get('ITEM')} | Merged: {d.get('merged_from_docs')} | Rule: {d.get('merge_rule')}")
        print(f"  Sample Items: {d.get('merge_items', [])[:2]}...")

if __name__ == "__main__":
    analyze_merges()
