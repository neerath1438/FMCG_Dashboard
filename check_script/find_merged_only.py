from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017").replace("mongodb:27017", "localhost:27017"))
db = client["fmcg_mastering"]
coll = db["MASTER_STOCK"]

# Find documents where merged_upcs has more than 1 item
query = { "merged_upcs.1": { "$exists": True } }
projection = { "ITEM": 1, "merged_upcs": 1, "_id": 0 }

results = list(coll.find(query, projection))

print(f"Total Merged Products Found: {len(results)}\n")
for idx, res in enumerate(results, 1):
    print(f"{idx}. Product: {res.get('ITEM')}")
    print(f"   Merged UPCs: {res.get('merged_upcs')}")
    print("-" * 30)
