from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]
src_coll = db["SINGLE_STOCK"]

oreo_docs = list(src_coll.find({"ITEM": "OREO VANILLA 133G"}))
print(f"Total OREO VANILLA 133G in SINGLE_STOCK: {len(oreo_docs)}")

# Checking how many markets
markets = set(d.get("Markets") for d in oreo_docs)
print(f"Unique Markets: {markets}")

# Checking Facts
facts = set(d.get("Facts") for d in oreo_docs)
print(f"Unique Facts: {facts}")
