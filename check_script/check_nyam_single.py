from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
single = db["single_stock_data"]

docs = list(single.find({"ITEM": {"$regex": "NYAM NYAM", "$options": "i"}}))

with open("d:/FMCG_Dashboard/nyam_single_results.txt", "w") as f:
    f.write(f"=== SINGLE STOCK DATA CHECK (NYAM NYAM) - {len(docs)} items found ===\n")
    for d in docs:
        f.write(f"ITEM: {d.get('ITEM')}\n")
        f.write(f"  UPC: {d.get('UPC')}\n")
        merge_items = d.get('merge_items', [])
        f.write(f"  MERGED ITEMS ({len(merge_items)}):\n")
        for mi in merge_items:
            f.write(f"    - {mi}\n")
        f.write("-" * 30 + "\n")
