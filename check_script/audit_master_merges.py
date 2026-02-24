from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']

q = {'Markets': 'Pen Malaysia', 'Facts': 'Sales Value'}
q_low = {'MARKETS': 'Pen Malaysia', 'FACTS': 'Sales Value'} # Try lowercase field names too Just in case

print("Checking master_stock_data...")
total = db['master_stock_data'].count_documents({})
nielsen_total = db['master_stock_data'].count_documents(q)
nielsen_total_low = db['master_stock_data'].count_documents(q_low)

print(f"Total Master Stock: {total}")
print(f"Nielsen (Markets/Facts): {nielsen_total}")
print(f"Nielsen (MARKETS/FACTS): {nielsen_total_low}")

# Check merged_from_docs field
has_merged_field = db['master_stock_data'].count_documents({'merged_from_docs': {'$exists': True}})
gt_1 = db['master_stock_data'].count_documents({'merged_from_docs': {'$gt': 1}})
eq_1 = db['master_stock_data'].count_documents({'merged_from_docs': 1})
is_string = db['master_stock_data'].count_documents({'merged_from_docs': {'$type': 'string'}})

print(f"Docs with merged_from_docs: {has_merged_field}")
print(f"Docs with merged_from_docs > 1: {gt_1}")
print(f"Docs with merged_from_docs == 1: {eq_1}")
print(f"Docs with merged_from_docs as string: {is_string}")

# If they are strings, check string > "1"
if is_string > 0:
    gt_1_str = db['master_stock_data'].count_documents({'merged_from_docs': {'$ne': "1"}})
    print(f"Docs with merged_from_docs (string) != '1': {gt_1_str}")

# Check specific Nielsen query merges
merged_nielsen = db['master_stock_data'].count_documents({**q, 'merged_from_docs': {'$gt': 1}})
print(f"Nielsen Merged docs: {merged_nielsen}")

# Find a sample merged doc
sample = db['master_stock_data'].find_one({'merged_from_docs': {'$gt': 1}})
if sample:
    print("\nSample Merged Doc:")
    print(f"ITEM: {sample.get('ITEM')}")
    print(f"merged_from_docs: {sample.get('merged_from_docs')} (Type: {type(sample.get('merged_from_docs'))})")
else:
    print("\nNo merged docs found with current query.")
