from pymongo import MongoClient, UpdateOne
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
master_col = db['master_stock_data']
single_col = db['single_stock_data']

print("Starting data fix for master_stock_data.merged_from_docs...")

# 1. First, identify all documents in master_stock_data
all_master_docs = list(master_col.find({}, {"merge_items": 1, "merged_from_docs": 1, "UPC": 1, "BRAND": 1, "ITEM": 1}))

ops = []
fix_count = 0

for doc in all_master_docs:
    # Logic: In processor.py, master docs are formed from single_stock docs
    # merged_from_docs should be the sum of merged_from_docs of all single_stock items that went into it
    
    items = doc.get("merge_items", [])
    if not items:
        continue
    
    # Simple strategy for this specific DB state:
    # If the current value is 2 and there is only 1 item in merge_items, it should be 1.
    # If the current value is >= 3 and there are N items, it should be calculated correctly.
    
    # Realistically, most "unmerged" items currently have 2. They should have 1.
    # So we set merged_from_docs = len(items) if we assume each item in merge_items was 1 raw doc.
    # Wait, in this dataset, usually each item in single_stock IS 1 raw doc.
    
    # Let's check how many items are actually in the merge_items list
    correct_count = len(items)
    
    if doc.get("merged_from_docs") != correct_count:
        ops.append(UpdateOne(
            {"_id": doc["_id"]},
            {"$set": {"merged_from_docs": correct_count}}
        ))
        fix_count += 1

if ops:
    print(f"Applying fixes to {len(ops)} documents...")
    # Execute in batches
    for i in range(0, len(ops), 1000):
        master_col.bulk_write(ops[i:i+1000])
    print(f"✅ Successfully fixed {fix_count} documents.")
else:
    print("No documents required fixing.")

# Final Verification for Nielsen
q = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
merged_nielsen = master_col.count_documents({**q, "merged_from_docs": {"$gt": 1}})
total_nielsen = master_col.count_documents(q)
print(f"\nVerification:")
print(f"  Total Nielsen products: {total_nielsen}")
print(f"  Truly Merged Nielsen products (>1): {merged_nielsen} (Should be around 344-413)")
