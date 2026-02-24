from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

print("Extracting exact fields for PETIT Q...")
p = col.find_one({'ITEM': {'$regex': 'PETIT Q', '$options': 'i'}})

if p:
    print(f"ITEM: {p.get('ITEM')}")
    print(f"merged_from_docs: {p.get('merged_from_docs')}")
    print(f"Facts: {p.get('Facts')}")
    print(f"Markets: {p.get('Markets')}")
    print(f"FACTS: {p.get('FACTS')}")
    print(f"MARKETS: {p.get('MARKETS')}")
    
    # Check for whitespace OR hidden characters
    if p.get('Facts'):
        print(f"Facts length: {len(p.get('Facts'))}")
        print(f"Facts repr: {repr(p.get('Facts'))}")
    if p.get('Markets'):
        print(f"Markets length: {len(p.get('Markets'))}")
        print(f"Markets repr: {repr(p.get('Markets'))}")

    # Check the actual count for this ITEM
    same_item_count = col.count_documents({'ITEM': p.get('ITEM')})
    print(f"\nTotal documents with this exact ITEM name: {same_item_count}")
else:
    print("PETIT Q not found.")
