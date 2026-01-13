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

doc = coll.find_one()
if doc:
    # Convert ObjectId to str
    doc["_id"] = str(doc["_id"])
    print(json.dumps(doc, indent=2))
else:
    print("NO DOC FOUND")
