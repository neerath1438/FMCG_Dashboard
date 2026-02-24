from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

q = {"Markets": "Pen Malaysia", "Facts": "Sales Value"}

print("Checking query counts for Nielsen Malaysia...")

# 1. Using merged_from_docs > 1
count_docs_gt_1 = col.count_documents({**q, "merged_from_docs": {"$gt": 1}})
print(f"1. merged_from_docs > 1: {count_docs_gt_1}")

# 2. Using size of merge_items > 1
count_size_gt_1 = col.count_documents({
    **q, 
    "$expr": {"$gt": [{"$size": {"$ifNull": ["$merge_items", []]}}, 1]}
})
print(f"2. size of merge_items > 1: {count_size_gt_1}")

# Total Reduction Calculation
pipeline = [
    {"$match": q},
    {"$project": {
        "item_count": {"$size": {"$ifNull": ["$merge_items", []]}},
        "docs_field": "$merged_from_docs"
    }},
    {"$group": {
        "_id": None,
        "total_reduction_by_size": {"$sum": {"$subtract": ["$item_count", 1]}},
        "total_reduction_by_field": {"$sum": {"$subtract": ["$docs_field", 1]}},
        "total_merged_groups": {"$sum": {"$cond": [{"$gt": ["$item_count", 1]}, 1, 0]}}
    }}
]

stats = list(col.aggregate(pipeline))
if stats:
    res = stats[0]
    print(f"\nAggregate Stats:")
    print(f"  Merged Groups Found: {res.get('total_merged_groups')}")
    print(f"  Total Reduction (by size): {res.get('total_reduction_by_size')}")
    print(f"  Total Reduction (by field): {res.get('total_reduction_by_field')}")
else:
    print("\nNo stats found.")
