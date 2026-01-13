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

# Find all rows for a master product
prod_name = "GLICO CHOCO BANANA 25GM"
docs = list(tgt_coll.find({"ITEM": prod_name}))
print(f"Total rows for {prod_name}: {len(docs)}")

for d in docs:
    print(f"Market: {d.get('Markets')} | MPack: {d.get('MPACK')} | Fact: {d.get('Facts')} | Merged UPCs: {len(d.get('merged_upcs', []))}")

