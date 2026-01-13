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

docs = list(master_coll.find().limit(5))
all_keys = set()
for d in docs:
    all_keys.update(d.keys())

print(f"All Unique Keys in first 5 docs: {sorted(list(all_keys))}")

# Print one doc as JSON
if docs:
    import json
    doc = docs[0]
    if '_id' in doc: doc['_id'] = str(doc['_id'])
    print("\nSample Document:")
    print(json.dumps(doc, indent=2))
