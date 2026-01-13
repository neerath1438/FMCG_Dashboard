from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
dbs = client.list_database_names()

target_count = 12288

for db_name in dbs:
    db = client[db_name]
    colls = db.list_collection_names()
    for c in colls:
        count = db[c].count_documents({})
        if count == target_count:
            print(f"MATCH: DB '{db_name}' | Collection '{c}' | Count: {count}")
        elif abs(count - target_count) < 20:
             print(f"CLOSE MATCH: DB '{db_name}' | Collection '{c}' | Count: {count}")
