from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

docs = list(master.find({"ITEM": {"$regex": "NYAM NYAM", "$options": "i"}}))

with open("d:/FMCG_Dashboard/final_verification_nyam.txt", "w") as f:
    f.write(f"=== FINAL VERIFICATION: NYAM NYAM SEPARATION ===\n")
    f.write(f"Total Master Items found: {len(docs)}\n\n")
    for d in docs:
        f.write(f"MASTER ITEM: {d.get('ITEM')}\n")
        f.write(f"  UPC: {d.get('UPC')}\n")
        f.write(f"  BRAND: {d.get('BRAND')}\n")
        f.write(f"  MERGED COUNT: {len(d.get('merge_items', []))}\n")
        f.write("-" * 30 + "\n")
