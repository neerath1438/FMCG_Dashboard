from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
cache = db["LLM_CACHE_STORAGE"]

items = [
    "NYAM NYAM RICE CRISPY 18GM",
    "ARNOTT'S NYAM NYAM RICE CRISPY 22 GM",
    "NYAM NYAM RICE CRISPY 22G",
    "NYAMNYAM RICE CRISPY 25GM"
]

with open("d:/FMCG_Dashboard/cache_merge_results.txt", "w") as f:
    f.write("=== LLM CACHE CHECK FOR SIZE-BASED MERGING ===\n")
    for item in items:
        doc = cache.find_one({"item": item})
        if not doc:
            doc = cache.find_one({"item": {"$regex": item.replace("'", "."), "$options": "i"}})
        
        if doc:
            res = doc.get("result", {})
            f.write(f"[{item}] (Matched: {doc['item']})\n")
            f.write(f"  base_item: {res.get('base_item')}\n")
            f.write(f"  flavour:   {res.get('flavour')}\n")
            f.write(f"  size:      {res.get('size')}\n")
        else:
            f.write(f"[{item}] NOT FOUND IN CACHE\n")
        f.write("-" * 20 + "\n")
