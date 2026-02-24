from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

q = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}

print(f"Auditing first 10 Nielsen Title Case records ({q})...")
docs = list(col.find(q).limit(10))

for i, d in enumerate(docs):
    val = d.get("merged_from_docs")
    print(f"{i+1}. ITEM: {repr(d.get('ITEM'))} | merged_from_docs: {repr(val)} | Type: {type(val)}")

# Check how many have > 1
gt_1 = col.count_documents({**q, "merged_from_docs": {"$gt": 1}})
print(f"\nTotal in this set with merged_from_docs > 1: {gt_1}")

# Check how many have field missing
missing = col.count_documents({**q, "merged_from_docs": {"$exists": False}})
print(f"Total in this set with merged_from_docs missing: {missing}")

# Check value 1
eq_1 = col.count_documents({**q, "merged_from_docs": 1})
print(f"Total in this set with merged_from_docs == 1: {eq_1}")
