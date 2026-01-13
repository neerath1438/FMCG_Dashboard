from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["fmcg_mastering"]

print("=" * 60)
print("CHECKING WHY LLM FAILED")
print("=" * 60)

# Get a low confidence item
low_conf = db["MASTER_STOCK"].find_one({"is_low_confidence": True})

if low_conf:
    print("\nLow Confidence Product:")
    print(f"  merge_id: {low_conf.get('merge_id')}")
    print(f"  brand: '{low_conf.get('brand')}'")
    print(f"  base_product_name: '{low_conf.get('base_product_name')}'")
    print(f"  confidence: {low_conf.get('llm_confidence_min')}")
    
    # Check original data
    if low_conf.get('merge_items'):
        original = low_conf['merge_items'][0]
        print(f"\nOriginal Data:")
        print(f"  UPC: {original.get('UPC')}")
        print(f"  Product Name: {original.get('Product Name')}")
        print(f"  Description: {original.get('Description')}")
        
        # Show all keys
        print(f"\nAll columns in original data:")
        for key in original.keys():
            print(f"    - {key}: {original[key]}")

print("\n" + "=" * 60)
