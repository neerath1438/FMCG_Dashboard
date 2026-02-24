from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

q_nielsen = {
    '$or': [
        {'Facts': {'$regex': '^Sales Value', '$options': 'i'}}, 
        {'FACTS': {'$regex': '^Sales Value', '$options': 'i'}}
    ]
}

print("NIELSEN MERGE STATISTICS:")
# Distribution of merged_from_docs
pipe = [
    {'$match': q_nielsen},
    {'$group': {'_id': '$merged_from_docs', 'count': {'$sum': 1}}},
    {'$sort': {'_id': 1}}
]
for row in col.aggregate(pipe):
    print(f"merged_from_docs: {row['_id']} | Count: {row['count']}")

# Count where merge_items exists and has length > 1
pipe_items = [
    {'$match': q_nielsen},
    {'$project': {'merge_items_count': {'$size': {'$ifNull': ['$merge_items', []]}}}},
    {'$group': {'_id': '$merge_items_count', 'count': {'$sum': 1}}},
    {'$sort': {'_id': 1}}
]
print("\nNIELSEN MERGE_ITEMS SIZE DISTRIBUTION:")
for row in col.aggregate(pipe_items):
    print(f"merge_items size: {row['_id']} | Count: {row['count']}")

# Sample product for testing detail view
merged_product = col.find_one({**q_nielsen, 'merged_from_docs': {'$gt': 1}})
if merged_product:
    print(f"\nSample Merged Product Found:")
    print(f"  _id: {merged_product['_id']}")
    print(f"  merge_id: {merged_product.get('merge_id')}")
    print(f"  ITEM: {merged_product.get('ITEM')}")
    print(f"  merged_from_docs: {merged_product.get('merged_from_docs')}")
    print(f"  merge_items: {merged_product.get('merge_items')}")
else:
    print("\nNo merged products found for Nielsen.")
