from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

# Try exact match
q_exact = {"Markets": "Pen Malaysia", "Facts": "Sales Value"}
# Try regex match (ignoring spaces)
q_regex = {
    "Markets": {"$regex": "^Pen Malaysia\\s*$", "$options": "i"},
    "Facts": {"$regex": "^Sales Value\\s*$", "$options": "i"}
}

count_exact = col.count_documents(q_exact)
count_regex = col.count_documents(q_regex)

print(f"Count with exact match: {count_exact}")
print(f"Count with regex match: {count_regex}")

# Check reduction
pipeline = [
    {"$match": q_regex},
    {"$project": {
        "merged_from_docs": {"$ifNull": ["$merged_from_docs", 1]}
    }},
    {"$group": {
        "_id": None,
        "count": {"$sum": 1},
        "merged_count": {"$sum": {"$cond": [{"$gt": ["$merged_from_docs", 1]}, 1, 0]}},
        "reduction": {"$sum": {"$subtract": ["$merged_from_docs", 1]}}
    }}
]

stats = list(col.aggregate(pipeline))
if stats:
    res = stats[0]
    print(f"\nFinal Stats (using regex):")
    print(f"  Total Products: {res.get('count')}")
    print(f"  Merged Products Count: {res.get('merged_count')}")
    print(f"  Total Reduction (Sum of merged docs - 1): {res.get('reduction')}")
else:
    print("\nNo Nielsen records found with regex.")
