from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
raw = db["single_stock_data"]

items_to_check = [
    "ARNOTT'S NYAM NYAM RICE CRISPY 22 GM",
    "ARNOTT'S NYAM NYAM FANTASY STICK 22.5 GM",
    "NYAM NYAM SPARK CHOCO 22.5G",
    "NYAM NYAM FANTASY STICK SPA CHOCO 25GM",
    "ARNOTT'S NYAM NYAM SUGAR RICE 27 GM",
    "ARNOTT'S NYAM-NYAM CHOC.SNACK SUGAR RICE 30 GM"
]

with open("d:/FMCG_Dashboard/nyam_upc_results.txt", "w") as f:
    for item in items_to_check:
        docs = list(raw.find({"ITEM": item}))
        if not docs:
            docs = list(raw.find({"ITEM": {"$regex": item, "$options": "i"}}))
        
        if docs:
            upcs = set(str(d.get("UPC", d.get("upc", "NO UPC"))) for d in docs)
            f.write(f"[{item}] -> UPCs: {upcs}\n")
        else:
            f.write(f"[{item}] -> NOT FOUND\n")
