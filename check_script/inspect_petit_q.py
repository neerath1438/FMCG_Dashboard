from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

# Search for the product from the screenshot
print("Searching for PETIT Q...")
p = col.find_one({'ITEM': {'$regex': 'PETIT Q', '$options': 'i'}})

if p:
    print(f"Product Found: {p.get('ITEM')}")
    print("\nAll Fields:")
    for k, v in sorted(p.items()):
        print(f"  {k}: {v} (Type: {type(v)})")
else:
    print("Product PETIT Q not found in master_stock_data.")

# Final check: count all merged products in the collection regardless of secondary filters
total_merged = col.count_documents({'merged_from_docs': {'$gt': 1}})
print(f"\nTotal docs with merged_from_docs > 1: {total_merged}")
