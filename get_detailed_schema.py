from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client['fmcg_mastering']

def get_detailed_info(collection_name):
    collection = db[collection_name]
    doc = collection.find_one()
    
    # Get unique fields from first 100 docs to be sure
    all_keys = set()
    for d in collection.find().limit(100):
        all_keys.update(d.keys())
    
    info = {
        "sample": {k: str(v) for k, v in doc.items()} if doc else {},
        "all_detected_keys": sorted(list(all_keys)),
        "count": collection.count_documents({})
    }
    return info

results = {
    "7-eleven_data": get_detailed_info("7-eleven_data"),
    "master_stock_data": get_detailed_info("master_stock_data")
}

with open("db_schema_details.json", "w") as f:
    json.dump(results, f, indent=2)

print("Done writing to db_schema_details.json")
