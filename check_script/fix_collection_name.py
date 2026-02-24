from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]

# Check current state
colls = db.list_collection_names()
print(f"Current collections: {colls}")

# 1. Delete 'MASTER_STOCK' (the 1-doc one) if it exists
if "MASTER_STOCK" in colls:
    count = db["MASTER_STOCK"].count_documents({})
    if count == 1:
        print("Deleting 1-doc 'MASTER_STOCK' collection...")
        db["MASTER_STOCK"].drop()
    else:
        print(f"Warning: 'MASTER_STOCK' has {count} docs, not deleting.")

# 2. Rename 'MASTER_STOCK ' (the 12288-doc one) to 'MASTER_STOCK'
if "MASTER_STOCK " in db.list_collection_names():
    print("Renaming 'MASTER_STOCK ' to 'MASTER_STOCK'...")
    db["MASTER_STOCK "].rename("MASTER_STOCK")
    print("Rename successful.")
else:
    print("'MASTER_STOCK ' (with space) not found via list_collection_names.")
    # Search for it explicitly if it was hidden
    for c in db.list_collection_names():
        if c == "MASTER_STOCK ":
             db[c].rename("MASTER_STOCK")
             print(f"Renamed {repr(c)} to 'MASTER_STOCK'")

# Final Check
print(f"Final collections: {db.list_collection_names()}")
count = db["MASTER_STOCK"].count_documents({})
print(f"Final Count for 'MASTER_STOCK': {count}")
