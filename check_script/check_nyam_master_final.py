from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

docs = list(master.find({"ITEM": {"$regex": "NYAM NYAM", "$options": "i"}}))

with open("d:/FMCG_Dashboard/nyam_master_final.txt", "w") as f:
    f.write(f"=== FINAL MASTER DATA CHECK (NYAM NYAM) - {len(docs)} items found ===\n")
    for d in docs:
        f.write(f"ITEM: {d.get('ITEM')}\n")
        f.write(f"  UPC: {d.get('UPC')}\n")
        merge_items = d.get('merge_items', [])
        f.write(f"  MERGED COUNT: {len(merge_items)}\n")
        f.write(f"  SAMPLE MERGED: {merge_items[:2]}\n")
        f.write("-" * 30 + "\n")
