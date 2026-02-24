from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']

# Query for Nielsen Malaysia data
nielsen_query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}

master_stock_coll = db['master_stock_data']

# Total master stock
total = master_stock_coll.count_documents(nielsen_query)

# Merged products (merged_from_docs > 1)
merged = master_stock_coll.count_documents({
    **nielsen_query,
    "merged_from_docs": {"$gt": 1}
})

# Single items (merged_from_docs = 1)
single_items = master_stock_coll.count_documents({
    **nielsen_query,
    "merged_from_docs": 1
})

# Products with NO_MERGE in merge_level
no_merge = master_stock_coll.count_documents({
    **nielsen_query,
    "merge_level": {"$regex": "NO_MERGE"}
})

# Products without merged_from_docs field
no_field = master_stock_coll.count_documents({
    **nielsen_query,
    "merged_from_docs": {"$exists": False}
})

print("=" * 60)
print("MASTER STOCK ANALYSIS")
print("=" * 60)
print(f"\nTotal Master Stock: {total}")
print(f"\nMerged Products (merged_from_docs > 1): {merged}")
print(f"Single Items (merged_from_docs = 1): {single_items}")
print(f"NO_MERGE in merge_level: {no_merge}")
print(f"No merged_from_docs field: {no_field}")
print(f"\nVerification: {merged} + {single_items} + {no_field} = {merged + single_items + no_field}")
print(f"Should equal total: {total}")

# Sample merged product
print("\n" + "=" * 60)
print("SAMPLE MERGED PRODUCT")
print("=" * 60)
sample_merged = master_stock_coll.find_one({
    **nielsen_query,
    "merged_from_docs": {"$gt": 1}
})
if sample_merged:
    print(f"BRAND: {sample_merged.get('BRAND')}")
    print(f"ITEM: {sample_merged.get('ITEM')}")
    print(f"merged_from_docs: {sample_merged.get('merged_from_docs')}")
    print(f"merge_level: {sample_merged.get('merge_level')}")
    print(f"merge_rule: {sample_merged.get('merge_rule')}")
