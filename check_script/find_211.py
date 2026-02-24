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

print("DISTRIBUTION OF MERGED_FROM_DOCS FOR NIELSEN:")
pipe = [
    {'$match': q_nielsen},
    {'$group': {'_id': '$merged_from_docs', 'count': {'$sum': 1}}},
    {'$sort': {'_id': 1}}
]
for row in col.aggregate(pipe):
    print(f"merged_from_docs: {row['_id']} | Count: {row['count']}")

print("\nMERGE RULES FOR MERGED PRODUCTS (>1):")
pipe_rules = [
    {'$match': {**q_nielsen, 'merged_from_docs': {'$gt': 1}}},
    {'$group': {'_id': '$merge_rule', 'count': {'$sum': 1}}}
]
for row in col.aggregate(pipe_rules):
    print(f"Rule: {row['_id']} | Count: {row['count']}")

print("\nCHECKING IF ANY COMBINATION GIVES 211:")
# Maybe items with merged_from_docs == 2?
exact_2 = col.count_documents({**q_nielsen, 'merged_from_docs': 2})
print(f"Count of products with merged_from_docs == 2: {exact_2}")

# Maybe items with merged_from_docs > 1 but only with Title Case fields?
q_title = {'Facts': {'$regex': '^Sales Value', '$options': 'i'}, 'Markets': {'$regex': '^Pen Malaysia', '$options': 'i'}}
merged_title = col.count_documents({**q_title, 'merged_from_docs': {'$gt': 1}})
print(f"Count of products with merged_from_docs > 1 (Title Case Only): {merged_title}")

# Maybe items with merged_from_docs > 1 but only with Upper Case fields?
q_upper = {'FACTS': {'$regex': '^Sales Value', '$options': 'i'}, 'MARKETS': {'$regex': '^Pen Malaysia', '$options': 'i'}}
merged_upper = col.count_documents({**q_upper, 'merged_from_docs': {'$gt': 1}})
print(f"Count of products with merged_from_docs > 1 (Upper Case Only): {merged_upper}")
