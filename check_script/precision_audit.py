from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

print("DEBUGGING FIELDS FOR PETIT Q...")
p = col.find_one({'ITEM': {'$regex': 'PETIT Q', '$options': 'i'}})

if p:
    print(f"ITEM: {repr(p.get('ITEM'))}")
    print("-" * 30)
    for k, v in sorted(p.items()):
        if k.upper() in ['FACTS', 'MARKETS', 'MERGED_FROM_DOCS']:
            print(f"KEY: {repr(k)} | VALUE: {repr(v)} | TYPE: {type(v)}")
    print("-" * 30)
    
    # Check all fields that contain "Market" or "Fact" regardless of case
    for k, v in sorted(p.items()):
        if 'MARKET' in k.upper() or 'FACT' in k.upper():
            print(f"MATCH: {repr(k)} -> {repr(v)}")

    # Total Count with THE EXACT VALUES WE FOUND
    # Assuming we find 'FACTS' and 'MARKETS'
    facts_val = p.get('FACTS')
    markets_val = p.get('MARKETS')
    print(f"\nSearching with EXACT values: FACTS={repr(facts_val)}, MARKETS={repr(markets_val)}")
    exact_count = col.count_documents({
        'FACTS': facts_val,
        'MARKETS': markets_val,
        'merged_from_docs': {'$gt': 1}
    })
    print(f"Exact Merged Count: {exact_count}")

else:
    print("PETIT Q not found.")
