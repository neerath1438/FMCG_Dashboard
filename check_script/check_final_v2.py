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
print(f"Total Rows: {len(docs)}")

# Map of Flavor -> List of Facts
groups = {}
for d in docs:
    name = d.get("ITEM")
    fact = d.get("Facts")
    groups.setdefault(name, []).append(fact)

for name, facts in groups.items():
    print(f"\nProduct: {name}")
    print(f"Facts Count: {len(facts)}")
    for f in sorted(facts):
        print(f" - {f}")

# Verify merge happened in at least one row
for d in docs:
    if len(d.get("merged_upcs", [])) > 1:
        print(f"\nLogic Verified: Merged {len(d.get('merged_upcs'))} UPCs into row with Fact: {d.get('Facts')}")
        break
