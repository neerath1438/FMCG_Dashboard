from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
brands = ["LOACKER", "NABATI", "OREO"]
for b in brands:
    total = db.master_stock_data.count_documents({"BRAND": b})
    missing = db.master_stock_data.count_documents({"BRAND": b, "$or": [{"product_form": None}, {"product_form": "UNKNOWN"}, {"product_form": ""}]})
    print(f"{b},{total},{missing}")
