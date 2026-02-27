from pymongo import MongoClient
import re

client = MongoClient('mongodb://localhost:27017/')
db = client['fmcg_mastering']
coll_master = db['master_stock_data']

search_terms = ["GOLDEN", "MOONCAKE", "LYCHEE", "ICE CREAM", "THINS", "MINI"]

print(f"{'ITEM':<60} | {'BRAND':<10} | {'VARIANT':<15}")
print("-" * 90)

for term in search_terms:
    print(f"\n--- Searching for: {term} ---")
    regex = re.compile(f".*{term}.*", re.IGNORECASE)
    items = list(coll_master.find({"BRAND": "OREO", "ITEM": regex}))
    for item in items:
        print(f"{item.get('ITEM', 'N/A')[:60]:<60} | {item.get('BRAND', 'N/A'):<10} | {item.get('VARIANT', 'N/A') or item.get('variant', 'N/A'):<15}")
