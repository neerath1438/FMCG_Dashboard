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

count_choc = master_coll.count_documents({"ITEM": {"$regex": "CHOC", "$options": "i"}})
print(f"Count for ITEM regex 'CHOC': {count_choc}")

if count_choc > 0:
    sample = master_coll.find_one({"ITEM": {"$regex": "CHOC", "$options": "i"}})
    print(f"Sample Chocolate ITEM: {sample.get('ITEM')}")
    sales_val = sample.get("MAT Nov'24")
    print(f"Sample MAT Nov'24: {sales_val}")
    print(f"Sample Facts: {sample.get('Facts')}")
