from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]
coll = db["MASTER_STOCK"]

facts = sorted(coll.distinct("Facts"))
print(f"ALL FACTS ({len(facts)}): {facts}")

print(f"\nIs 'Value' in facts? {'Value' in facts}")
print(f"Is 'Units' in facts? {'Units' in facts}")

if 'Value' not in facts:
    # Check if there is something SIMILAR
    v_matches = [f for f in facts if 'VALUE' in f.upper()]
    print(f"Similar to 'Value': {v_matches}")
