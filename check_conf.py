from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]
cache_coll = db["LLM_CACHE_STORAGE"]

items = ["OREO VANILLA 133G", "LEE GIFT CLASSIC ASSORTMENT BISCUITS 200GM"]
for item in items:
    cached = cache_coll.find_one({"item": item})
    if cached:
        res = cached["result"]
        print(f"Item: {item}")
        print(f"  Result: {res}")
    else:

        print(f"Item: {item} - NOT IN CACHE")
