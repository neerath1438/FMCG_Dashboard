from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client['fmcg_mastering']

for coll_name in db.list_collection_names():
    keys = set()
    for doc in db[coll_name].find().limit(500):
        keys.update(doc.keys())
    
    upc_keys = [k for k in keys if "UPC" in k.upper()]
    if upc_keys:
        print(f"Collection: {coll_name} | Keys: {upc_keys}")
