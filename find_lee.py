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

docs = list(src_coll.find({"ITEM": {"$regex": "LEE GIFT", "$options": "i"}}))
print(f"Found {len(docs)} Lee Gift items.")
for d in docs[:3]:
    print(f"- {d.get('ITEM')}")
