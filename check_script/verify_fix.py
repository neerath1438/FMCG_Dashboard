from pymongo import MongoClient
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

def check_fix():
    print("=== FMCG Dashboard Quick Fix Verification ===\n")

    # 1. Check Meiji Hello Panda (Should be separated by Form)
    print("Checking: Meiji/Hello Panda Separation")
    meiji_docs = list(master.find({"BRAND": "MEIJI", "ITEM": {"$regex": "HELLO PANDA", "$options": "i"}}))
    print(f"  Found {len(meiji_docs)} distinct master items for Hello Panda.")
    for d in meiji_docs:
        print(f"  -> Master Item: {d.get('ITEM')} (Merged from: {d.get('merged_from_docs')} docs)")

    # 2. Check Nabati (Should use BRAND='NABATI', not 'ROLLS')
    print("\nChecking: Nabati Brand Extraction & Form Separation")
    nabati_docs = list(master.find({"$or": [{"BRAND": "NABATI"}, {"ITEM": {"$regex": "NABATI", "$options": "i"}}]}))
    for d in nabati_docs:
        print(f"  -> Brand: {d.get('BRAND')} | Master Item: {d.get('ITEM')} (Merged from: {d.get('merged_from_docs')} docs)")

    # 3. Check for Flavor/Form mix (Look for groups containing both Wafer and Biscuit)
    print("\nChecking: Cross-Form Merging (The 'Bug' Check)")
    mixed_groups = list(master.find({
        "$and": [
            { "MERGE_ITEMS": { "$regex": "WAFER", "$options": "i" } },
            { "MERGE_ITEMS": { "$regex": "BISCUIT|STICK|ROLL", "$options": "i" } }
        ]
    }))
    
    if len(mixed_groups) == 0:
        print("  ✅ SUCCESS: No mixed product forms found in current master groups.")
    else:
        print(f"  ⚠️ WARNING: Found {len(mixed_groups)} groups that might still have mixed forms. Review needed.")
        for d in mixed_groups[:3]:
            print(f"     Group: {d.get('ITEM')} | Brand: {d.get('BRAND')}")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    check_fix()
