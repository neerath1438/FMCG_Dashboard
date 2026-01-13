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
coll = db["MASTER_STOCK"]

# Test the regex that I suspect might be used
queries_to_test = [
    {"ITEM": {"$regex": "CHOCOLATE", "$options": "i"}},
    {"ITEM": {"$regex": "CHOC", "$options": "i"}},
    {"BRAND": "OREO"},
    {"BRAND": {"$regex": "OREO", "$options": "i"}}
]

print(f"Total docs in MASTER_STOCK: {coll.count_documents({})}")

for q in queries_to_test:
    count = coll.count_documents(q)
    print(f"Query: {json.dumps(q)} | Match Count: {count}")

# Check one random document to see fields
sample = coll.find_one()
if sample:
    print(f"\nSample Fields: {list(sample.keys())}")
    print(f"Sample ITEM: {sample.get('ITEM')}")
    print(f"Sample BRAND: {sample.get('BRAND')}")
