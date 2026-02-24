from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    mongo_uri = mongo_uri.replace("mongodb:27017", "localhost:27017")

client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]
tgt_coll = db["MASTER_STOCK"]

docs = list(tgt_coll.find({}))
print(f"Total Master Stock Rows: {len(docs)}")

# Group by Item name to see counts
summary = {}
for d in docs:
    name = d.get("ITEM")
    summary.setdefault(name, []).append(d.get("Facts"))

for name, facts in summary.items():
    print(f"\nProduct: {name}")
    print(f"Number of Rows: {len(facts)}")
    print(f"Unique Facts: {len(set(facts))}")
    for f in sorted(list(set(facts))):
        print(f" - {f}")
