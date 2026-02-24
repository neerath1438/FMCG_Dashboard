from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
missing = list(db.master_stock_data.find({"$or": [{"product_form": None}, {"product_form": "UNKNOWN"}]}))
brands = {}
for d in missing:
    b = d.get("BRAND", "UNKNOWN")
    brands[b] = brands.get(b, 0) + 1
for b, c in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:20]:
    print(f"{b}: {c}")
