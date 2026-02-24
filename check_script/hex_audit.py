from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

print("PRECISION AUDIT FOR PETIT Q...")
p = col.find_one({'ITEM': {'$regex': 'PETIT Q', '$options': 'i'}})

if p:
    print(f"ITEM: {repr(p.get('ITEM'))}")
    
    # Audit FACTS (any case)
    for k in p.keys():
        if k.upper() == 'FACTS':
            val = p.get(k)
            print(f"FACTS KEY: {repr(k)}")
            print(f"FACTS VALUE: {repr(val)}")
            print(f"FACTS HEX: {val.encode().hex() if isinstance(val, str) else 'N/A'}")

    # Audit MARKETS (any case)
    for k in p.keys():
        if k.upper() == 'MARKETS':
            val = p.get(k)
            print(f"MARKETS KEY: {repr(k)}")
            print(f"MARKETS VALUE: {repr(val)}")
            print(f"MARKETS HEX: {val.encode().hex() if isinstance(val, str) else 'N/A'}")
            
    # Audit MERGED_FROM_DOCS (any case)
    for k in p.keys():
        if k.upper() == 'MERGED_FROM_DOCS':
            val = p.get(k)
            print(f"MERGE KEY: {repr(k)} | VALUE: {repr(val)} | TYPE: {type(val)}")

    # SEARCH WITH REGEX TO BE SAFE
    print("\nAttempting regex search for Sales Value and Pen Malaysia...")
    q_regex = {
        'FACTS': {'$regex': '^Sales Value', '$options': 'i'},
        'MARKETS': {'$regex': '^Pen Malaysia', '$options': 'i'},
        'merged_from_docs': {'$gt': 1}
    }
    regex_count = col.count_documents(q_regex)
    print(f"Regex Count (Starts with Sales Value/Pen Malaysia, Merged): {regex_count}")

else:
    print("PETIT Q not found.")
