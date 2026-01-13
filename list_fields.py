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
if doc:
    print("FIELDS FOUND IN MASTER_STOCK:")
    for key in doc.keys():
        print(f" - {key}")
else:
    print("NO DATA")
