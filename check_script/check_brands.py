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

brands = master_coll.distinct("BRAND")
print(f"Top 10 brands: {brands[:10]}")

# Also check for 'MAMEE' specifically
count = master_coll.count_documents({"BRAND": "MAMEE"})
print(f"Count for BRAND 'MAMEE': {count}")
if count == 0:
    # Try regex
    count_regex = master_coll.count_documents({"BRAND": {"$regex": "MAMEE", "$options": "i"}})
    print(f"Count for BRAND regex 'MAMEE': {count_regex}")
