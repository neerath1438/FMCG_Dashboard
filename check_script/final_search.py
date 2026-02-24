from pymongo import MongoClient
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

terms = ["MASTURA", "SNAZK", "EXCLUSIVE", "PRIVATE LABEL"]

for t in terms:
    print(f"\n--- Searching for {t} in Master ---")
    docs = list(master.find({"$or": [{"ITEM": {"$regex": t, "$options": "i"}}, {"MERGE_ITEMS": {"$regex": t, "$options": "i"}}]}, {"ITEM": 1, "BRAND": 1}))
    for d in docs:
        print(f"ITEM: {d.get('ITEM')}, BRAND: {d.get('BRAND')}")
