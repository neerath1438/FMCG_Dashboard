from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

# Count docs with merged_from_docs > 1
merged_count = col.count_documents({'merged_from_docs': {'$gt': 1}})
print(f"Total Merged Documents (merged_from_docs > 1): {merged_count}")

# Check casing for these merged docs
print("\nAuditing field casing for merged docs...")
has_title_case = col.count_documents({'merged_from_docs': {'$gt': 1}, 'Facts': {'$exists': True}})
has_upper_case = col.count_documents({'merged_from_docs': {'$gt': 1}, 'FACTS': {'$exists': True}})

print(f"Merged docs with Title Case 'Facts': {has_title_case}")
print(f"Merged docs with Upper Case 'FACTS': {has_upper_case}")

# Find Nielsen matches in both categories
q_title = {'Facts': 'Sales Value', 'Markets': 'Pen Malaysia'}
q_upper = {'FACTS': 'Sales Value', 'MARKETS': 'Pen Malaysia'}

merged_title_nielsen = col.count_documents({**q_title, 'merged_from_docs': {'$gt': 1}})
merged_upper_nielsen = col.count_documents({**q_upper, 'merged_from_docs': {'$gt': 1}})

print(f"\nNielsen Merged (Title Case): {merged_title_nielsen}")
print(f"Nielsen Merged (Upper Case): {merged_upper_nielsen}")

# Calculate total reduction for Nielsen
# Total reduction = Sum(merged_from_docs - 1)
pipeline = [
    {"$match": {"merged_from_docs": {"$gt": 1}}},
    # Match either Title Case OR Upper Case
    {"$match": {"$or": [q_title, q_upper]}},
    {"$group": {
        "_id": None,
        "count": {"$sum": 1},
        "reduction": {"$sum": {"$subtract": ["$merged_from_docs", 1]}}
    }}
]
stats = list(col.aggregate(pipeline))
if stats:
    print(f"\nFinal Statistics for Nielsen Merges:")
    print(f"  Resulting Merged Products: {stats[0].get('count')}")
    print(f"  Original Records Merged AWAY (Reduction): {stats[0].get('reduction')}")
else:
    print("\nNo Nielsen merges found with either casing.")
