from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["fmcg_mastering"]

print("=" * 60)
print("CLEARING ALL COLLECTIONS")
print("=" * 60)

# Drop all collections
collections = db.list_collection_names()
for coll_name in collections:
    db[coll_name].drop()
    print(f"Dropped: {coll_name}")

print(f"\nTotal collections dropped: {len(collections)}")
print("\nDatabase is now clean and ready for fresh upload!")
print("=" * 60)
