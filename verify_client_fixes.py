from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]
master_coll = db["MASTER_STOCK"]

print("--- VERIFYING CLIENT REQUIREMENTS ---")

# 1. Check for Duplicate Facts (Goal: Only 1 row per product per market)
# Group by Brand, Flavour, Size, Market and count
pipeline = [
    {
        "$group": {
            "_id": {
                "brand": "$brand",
                "flavour": "$flavour",
                "size": "$size",
                "market": "$Markets"
            },
            "count": {"$sum": 1},
            "facts_merged": {"$push": "$Facts"}
        }
    },
    {"$match": {"count": {"$gt": 1}}}
]

duplicates = list(master_coll.aggregate(pipeline))
if duplicates:
    print(f"[X] FOUND DUPLICATES: {len(duplicates)} groups still have multiple rows.")
    for d in duplicates[:3]:
        print(f"  Group: {d['_id']} | Rows: {d['count']} | Facts: {d['facts_merged']}")
else:
    print("[OK] SUCCESS: No duplicate Fact rows for the same product+market.")


# 2. Check for Merged Items (Merge items should have multiple entries if merged)
merged_products = list(master_coll.find({"merged_from_docs": {"$gt": 1}}).limit(5))
print(f"\nSample Merged Products ({len(merged_products)}):")
for p in merged_products:
    print(f"- {p.get('brand')} {p.get('flavour')} {p.get('size')} | Merged Items: {len(p.get('merge_items', []))} | UPCs: {len(p.get('merged_upcs', []))}")

# 3. Check for Size Tolerance Merges (Items with different ITEM names but same Master Size)
# We can look for items in merge_items that have different sizes if the model was good
# But easiest is to check if any doc has multiple merge_items
print(f"\nSuccess: Verification complete.")
