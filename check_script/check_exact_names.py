from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]
colls = db.list_collection_names()
for c in colls:
    if "MASTER_STOCK" in c:
        count = db[c].count_documents({})
        print(f"NAME: {repr(c)} | COUNT: {count}")
