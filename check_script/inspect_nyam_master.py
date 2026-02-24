from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

docs = list(master.find({"ITEM": {"$regex": "NYAM NYAM", "$options": "i"}}))

with open("d:/FMCG_Dashboard/nyam_master_check.txt", "w") as f:
    for d in docs:
        f.write(f"MASTER ITEM: {d.get('ITEM')}\n")
        f.write(f"  BRAND: {d.get('BRAND')}\n")
        merge_items = d.get('merge_items', d.get('MERGE_ITEMS', []))
        f.write(f"  MERGED ITEMS ({len(merge_items)}):\n")
        for mi in merge_items:
            f.write(f"    - {mi}\n")
        f.write("-" * 20 + "\n")
