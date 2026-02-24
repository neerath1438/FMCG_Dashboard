from pymongo import MongoClient
import os
from dotenv import load_dotenv
import re

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

# regex for Case Insensitive field values
val_facts = re.compile(f"^{re.escape('Sales Value')}\\s*$", re.I)
val_markets = re.compile(f"^{re.escape('Pen Malaysia')}\\s*$", re.I)

print("Auditing all Nielsen records regardless of field casing...")

all_docs = list(col.find({}))
nielsen_docs = []

for doc in all_docs:
    # Check all keys for Facts/Markets
    has_facts = False
    has_markets = False
    for k, v in doc.items():
        if k.upper() == 'FACTS' and isinstance(v, str) and val_facts.match(v):
            has_facts = True
        if k.upper() == 'MARKETS' and isinstance(v, str) and val_markets.match(v):
            has_markets = True
    
    if has_facts and has_markets:
        nielsen_docs.append(doc)

print(f"Total Nielsen docs found: {len(nielsen_docs)}")

merged_docs = [d for d in nielsen_docs if d.get('merged_from_docs', 1) > 1]
print(f"Merged Nielsen docs (merged_from_docs > 1): {len(merged_docs)}")

total_reduction = sum(d.get('merged_from_docs', 1) - 1 for d in nielsen_docs)
print(f"Total reduction (sum of merged_from_docs - 1): {total_reduction}")

if merged_docs:
    print("\nExample Merged Doc:")
    d = merged_docs[0]
    print(f"  ITEM: {d.get('ITEM')}")
    print(f"  Keys: {[k for k in d.keys() if k.upper() in ['FACTS', 'MARKETS']]}")
    print(f"  merged_from_docs: {d.get('merged_from_docs')}")
