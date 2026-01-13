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

doc = master_coll.find_one()
with open('debug_keys.txt', 'w', encoding='utf-8') as f:
    if doc:
        for k in sorted(doc.keys()):
            f.write(f"{k}\n")
    else:
        f.write("EMPTY")
