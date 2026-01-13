from pymongo import MongoClient
import os
import json
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

print(f"KEYS_JSON: {json.dumps(sorted(list(all_keys)))}")
