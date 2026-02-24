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

count_correct = master_coll.count_documents({"ITEM": {"$regex": "CHOCOLATE", "$options": "i"}})
print(f"Count for 'CHOCOLATE': {count_correct}")

count_typo = master_coll.count_documents({"ITEM": {"$regex": "CHOCALATE", "$options": "i"}})
print(f"Count for 'CHOCALATE': {count_typo}")
