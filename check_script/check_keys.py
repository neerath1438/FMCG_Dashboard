from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]
master_coll = db["MASTER_STOCK"]

sample = master_coll.find_one()
if sample:
    print(f"Keys: {list(sample.keys())}")
    print(f"Sample: {json.dumps({k: sample[k] for k in list(sample.keys())[:10] if k != '_id'}, indent=2)}")
else:
    print("MASTER_STOCK is empty")
