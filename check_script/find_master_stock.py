from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
dbs = client.list_database_names()

for db_name in dbs:
    db = client[db_name]
    colls = db.list_collection_names()
    if "MASTER_STOCK" in colls:
        count = db["MASTER_STOCK"].count_documents({})
        print(f"FOUND: DB '{db_name}' | Collection 'MASTER_STOCK' | Count: {count}")
    
    # Also check case insensitive
    for c in colls:
        if c.upper() == "MASTER_STOCK":
             count = db[c].count_documents({})
             print(f"FOUND (CASE): DB '{db_name}' | Collection '{c}' | Count: {count}")
