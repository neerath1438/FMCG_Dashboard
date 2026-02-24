from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client['fmcg_mastering']

def discover_schema(collection_name):
    print(f"\n--- Schema Discovery for {collection_name} ---")
    collection = db[collection_name]
    doc = collection.find_one()
    if doc:
        for key, value in doc.items():
            print(f"{key}: {type(value).__name__} (Sample: {value})")
    else:
        print("Collection is empty.")

discover_schema('7-eleven_data')
discover_schema('master_stock_data')
