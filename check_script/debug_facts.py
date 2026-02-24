from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["fmcg_mastering"]
collection = db["MASTER_STOCK"]

distinct_facts = collection.distinct("Facts")
print("Distinct Facts in MASTER_STOCK:")
for fact in distinct_facts:
    print(f"'{fact}'")

# Also check one document to see the structure
doc = collection.find_one({"Facts": {"$exists": True}})
if doc:
    print("\nSample Document Facts field:")
    print(f"Type: {type(doc['Facts'])}")
    print(f"Value: '{doc['Facts']}'")
