from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
brands = ["LOACKER", "NABATI", "OREO"]
for b in brands:
    print(f"--- Brand: {b} ---")
    distinct_forms = db.master_stock_data.distinct("product_form", {"BRAND": b})
    print(f"Distinct Forms: {distinct_forms}")
    missing_one = db.master_stock_data.find_one({"BRAND": b, "$or": [{"product_form": None}, {"product_form": "UNKNOWN"}, {"product_form": ""}]})
    if missing_one:
        print(f"Found a missing one: {missing_one.get('ITEM')} | Form: {missing_one.get('product_form')}")
    else:
        print("No missing ones found via find_one!")
