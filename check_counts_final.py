from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]
print(f"DATABASE: fmcg_mastering")
for coll_name in sorted(db.list_collection_names()):
    count = db[coll_name].count_documents({})
    print(f"COLL: {coll_name:30} | COUNT: {count}")
