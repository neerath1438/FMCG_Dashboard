from pymongo import MongoClient
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["fmcg_mastering"]

MASTER_STOCK_COL = "master_stock_data"

print("=" * 60)
print(f"INSPECTING {MASTER_STOCK_COL}")
print("=" * 60)

coll = db[MASTER_STOCK_COL]
count = coll.count_documents({})
print(f"Total documents: {count}")

if count > 0:
    sample = coll.find_one()
    print("\nSample Document Keys:")
    for key in sorted(sample.keys()):
        print(f"  - {key} (type: {type(sample[key]).__name__})")
    
    # Check for monthly columns
    monthly_cols = [k for k in sample.keys() if "w/e" in k.lower() or "mat" in k.lower()]
    print(f"\nMonthly Columns found: {len(monthly_cols)}")
    for col in monthly_cols[:5]:
        print(f"  - {col}")
    if len(monthly_cols) > 5:
        print(f"  ... and {len(monthly_cols) - 5} more")
else:
    print("\nCollection is empty")

print("\n" + "=" * 60)
