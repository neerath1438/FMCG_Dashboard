from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
raw = db["raw_data"]

missing_brands = ['EXCLUSIVE BRAND', 'MASUYA', 'PRIVATE LABEL', 'SNAZK']

for rb in missing_brands:
    docs = list(raw.find({"BRAND": rb}).limit(2))
    print(f"BRAND: {rb}")
    for d in docs:
        print(f"  Item: {d.get('ITEM')}, UPC: {d.get('UPC')}")
