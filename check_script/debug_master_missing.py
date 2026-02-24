from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

# Broad search for ANY Nyam Nyam items to see what fields they have
sample = master.find_one({"ITEM": {"$regex": "NYAM", "$options": "i"}})

with open("d:/FMCG_Dashboard/debug_master_results.txt", "w") as f:
    f.write("--- SAMPLE DOC ---\n")
    if sample:
        for k, v in sample.items():
            if k != "merge_items":
                f.write(f"{k}: {v} ({type(v)})\n")
        f.write(f"Merge items count: {len(sample.get('merge_items', []))}\n")
    else:
        f.write("No Nyam Nyam doc found in master_stock_data!\n")

    # Check merged_upcs
    sample_upc = master.find_one({"merged_upcs": "8886015402037"})
    f.write(f"Found by merged_upcs: {'Yes' if sample_upc else 'No'}\n")
    
    if sample_upc:
        f.write(f"Item found by merged_upcs: {sample_upc.get('ITEM')}\n")
        f.write(f"Fields in found doc: {list(sample_upc.keys())}\n")

# Check if items are currently being processed (Flow 2 might be slow)
total_master = master.count_documents({})
total_single = db["single_stock_data"].count_documents({})
print(f"Total Master Count: {total_master} / {total_single}")
