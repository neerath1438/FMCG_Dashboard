from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

# Search for Nyam Nyam variants
variants = ["RICE CRISPY", "FANTASY STICK", "SUGAR RICE"]

with open("d:/FMCG_Dashboard/nyam_status_report.txt", "w") as f:
    f.write("=== NYAM NYAM MASTER STATUS REPORT ===\n\n")
    for v in variants:
        docs = list(master.find({"ITEM": {"$regex": v, "$options": "i"}}))
        f.write(f"--- VARIANT: {v} ({len(docs)} master items) ---\n")
        for d in docs[:5]: # Show first 5 of each
            f.write(f"ITEM: {d.get('ITEM')}\n")
            f.write(f"  UPC:  {d.get('UPC')} (Type: {type(d.get('UPC'))})\n")
            f.write(f"  MERGED: {d.get('merged_from_docs')}\n")
            f.write(f"  NORM_ITEM: {d.get('normalized_item')}\n")
            f.write("-" * 20 + "\n")
        f.write("\n")
