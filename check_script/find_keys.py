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

all_keys = set()
for doc in master_coll.find().limit(100):
    all_keys.update(doc.keys())

patterns = ["BRAND", "ITEM", "MARKET", "FACT", "PACK", "PRODUCT", "DESCRIPTION"]
found = []
for k in all_keys:
    if any(p in k.upper() for p in patterns):
        found.append(k)

print(f"Matched Keys: {found}")

# Also just print every key one by one to a file
with open('all_keys.txt', 'w') as f:
    for k in sorted(list(all_keys)):
        f.write(f"{k}\n")
