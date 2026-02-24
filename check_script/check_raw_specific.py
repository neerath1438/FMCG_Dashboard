from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
raw = db["raw_data"]

to_check = ['EXCLUSIVE BRAND', 'PRIVATE LABEL', 'MASUYA']

for b in to_check:
    print(f"\n--- {b} ---")
    for doc in raw.find({"BRAND": b}).limit(2):
        print(f"ITEM: {doc.get('ITEM')}, UPC: {doc.get('UPC')}")
