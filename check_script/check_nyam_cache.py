from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
cache_coll = db["LLM_CACHE_STORAGE"]

items_to_check = [
    "ARNOTT'S NYAM NYAM RICE CRISPY 22 GM",
    "ARNOTT'S NYAM NYAM FANTASY STICK 22.5 GM",
    "NYAM NYAM SPARK CHOCO 22.5G",
    "NYAM NYAM FANTASY STICK SPA CHOCO 25GM",
    "ARNOTT'S NYAM NYAM SUGAR RICE 27 GM",
    "ARNOTT'S NYAM-NYAM CHOC.SNACK SUGAR RICE 30 GM"
]

print("=== LLM CACHE CHECK FOR NYAM NYAM ===")
with open("d:/FMCG_Dashboard/nyam_results.txt", "w") as f:
    for item in items_to_check:
        doc = cache_coll.find_one({"item": item})
        if doc:
            res = doc.get("result", {})
            f.write(f"[{item}] -> BASE: {res.get('base_item')} | FLV: {res.get('flavour')} | CONF: {res.get('confidence')}\n")
        else:
            f.write(f"[{item}] -> MISSING\n")
