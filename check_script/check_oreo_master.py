from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]
tgt_coll = db["MASTER_STOCK"]

oreo_docs = list(tgt_coll.find({"ITEM": "OREO VANILLA 133G"}))
print(f"Total OREO VANILLA 133G in MASTER_STOCK: {len(oreo_docs)}")

for d in oreo_docs:
    print(f"Market: {d.get('Markets')} | Facts: {d.get('Facts')} | Merged from: {d.get('merged_from_docs')} items")
