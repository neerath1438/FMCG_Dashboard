from pymongo import MongoClient
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

search_terms = ["SNAZK", "MASUYA", "PRIVATE LABEL", "EXCLUSIVE BRAND"]

for term in search_terms:
    docs = list(master.find({"$or": [{"ITEM": {"$regex": term, "$options": "i"}}, {"MERGE_ITEMS": {"$regex": term, "$options": "i"}}]}, {"ITEM": 1, "BRAND": 1}))
    print(f"SEARCH: {term}")
    for d in docs:
        print(f"  Found: {d.get('ITEM')}, BRAND: {d.get('BRAND')}")
