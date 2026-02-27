from pymongo import MongoClient
import re

client = MongoClient('mongodb://localhost:27017/')
db = client['fmcg_mastering']
coll_master = db['master_stock_data']

print("--- Detailed Check for Mocha ---")
results = list(coll_master.find({"ITEM": {"$regex": "MOCHA", "$options": "i"}}))
for r in results:
    print(f"ITEM: {r.get('ITEM')}")
    print(f"UPC: {r.get('UPC')}")
    print(f"MPACK: {r.get('MPACK')}")
    print(f"BRAND: {r.get('BRAND')}")
    print(f"VARIANT: {r.get('VARIANT') or r.get('variant')}")
    print(f"NRMSIZE: {r.get('NRMSIZE')}")
    print("-" * 20)

print("\n--- Detailed Check for Lychee Orange ---")
results = list(coll_master.find({"ITEM": {"$regex": "LYCHEE", "$options": "i"}}))
for r in results:
    print(f"ITEM: {r.get('ITEM')}")
    print(f"UPC: {r.get('UPC')}")
    print(f"MPACK: {r.get('MPACK')}")
    print(f"BRAND: {r.get('BRAND')}")
    print("-" * 20)
