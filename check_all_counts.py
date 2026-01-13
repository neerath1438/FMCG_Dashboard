from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
print(f"Connecting to: {mongo_uri}")
dbs = client.list_database_names()
print(f"Databases: {dbs}")

for db_name in ["fmcg_mastering", "test", "admin"]:
    if db_name in dbs:
        db = client[db_name]
        print(f"\n--- Database: {db_name} ---")
        colls = db.list_collection_names()
        for coll_name in colls:
            count = db[coll_name].count_documents({})
            print(f"Collection: {coll_name} | Documents: {count}")
