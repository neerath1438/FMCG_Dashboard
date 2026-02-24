from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(uri)

print(f"Connected to: {uri}")
dbs = client.list_database_names()
print(f"Databases: {dbs}")

for db_name in dbs:
    db = client[db_name]
    colls = db.list_collection_names()
    print(f"  DB: {db_name} | Collections: {colls}")
    for coll_name in colls:
        count = db[coll_name].count_documents({})
        if count > 0:
            print(f"    - {coll_name}: {count} documents")
