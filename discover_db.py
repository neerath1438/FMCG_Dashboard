from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client['fmcg_mastering']

def get_samples(collection_name):
    print(f"\n--- Samples from {collection_name} ---")
    collection = db[collection_name]
    samples = list(collection.find().limit(5))
    for sample in samples:
        # Convert ObjectId to string for printing
        sample['_id'] = str(sample['_id'])
        print(json.dumps(sample, indent=2))
        print("-" * 20)

get_samples('7-eleven_data')
get_samples('master_stock_data')
