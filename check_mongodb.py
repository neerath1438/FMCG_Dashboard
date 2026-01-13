from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["fmcg_mastering"]

print("=" * 60)
print("MONGODB COLLECTIONS STATUS")
print("=" * 60)

# List all collections
collections = db.list_collection_names()
print(f"\nTotal Collections: {len(collections)}\n")

for coll_name in collections:
    count = db[coll_name].count_documents({})
    print(f"{coll_name}: {count} documents")

print("\n" + "=" * 60)
print("MASTER_STOCK SAMPLE DATA")
print("=" * 60)

# Show sample from MASTER_STOCK
if "MASTER_STOCK" in collections:
    sample = db["MASTER_STOCK"].find_one()
    if sample:
        print(f"\nSample Document:")
        print(f"  merge_id: {sample.get('merge_id')}")
        print(f"  brand: {sample.get('brand')}")
        print(f"  flavour: {sample.get('flavour')}")
        print(f"  size: {sample.get('size')}")
        print(f"  merged_upcs: {sample.get('merged_upcs')}")
        print(f"  merged_from_docs: {sample.get('merged_from_docs')}")
        print(f"  llm_confidence_min: {sample.get('llm_confidence_min')}")
        print(f"  is_low_confidence: {sample.get('is_low_confidence')}")
    else:
        print("\nMASTER_STOCK is empty")
else:
    print("\nMASTER_STOCK collection not found")

print("\n" + "=" * 60)
