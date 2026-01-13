from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Determine MONGO_URI for local testing
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]

master_coll = db["MASTER_STOCK"]

print(f"Total documents in MASTER_STOCK: {master_coll.count_documents({})}")

sample = master_coll.find_one()
if sample:
    print("\nSample Document Keys:")
    print(list(sample.keys()))
    
    print("\nUnique Brands (Top 10):")
    brands = master_coll.distinct("brand")
    print(brands[:10])
    
    print("\nUnique Flavours (Top 10):")
    flavours = master_coll.distinct("flavour")
    print(flavours[:10])
    
    print("\nUnique Sizes (Top 10):")
    sizes = master_coll.distinct("size")
    print(sizes[:10])
    
    # Check for cases where brand/flavour might be missing
    print(f"\nDocuments with empty brand: {master_coll.count_documents({'brand': {'$in': ['', None]}})}")
    print(f"Documents with empty flavour: {master_coll.count_documents({'flavour': {'$in': ['', None]}})}")
    
else:
    print("\nMASTER_STOCK is empty!")
