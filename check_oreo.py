from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
items = list(db.master_stock_data.find({"BRAND": "OREO"}).limit(5))
for d in items:
    print(f"ITEM: {d.get('ITEM')} | FORM: {d.get('product_form')}")
