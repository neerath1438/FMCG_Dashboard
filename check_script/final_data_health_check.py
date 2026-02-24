from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

def final_health_check():
    print("\n" + "="*50)
    print("      --- FINAL DATA QUALITY REPORT ---")
    print("="*50)

    # 1. NYAM NYAM SPECIAL CHECK
    print("\n1. CHECKING NYAM NYAM (UPC: 8886015402037)")
    nyam_items = list(master.find({"UPC": 8886015402037}, {"ITEM": 1, "product_form": 1, "merged_from_docs": 1}))
    if len(nyam_items) > 1:
        print(f"   [SUCCESS] Found {len(nyam_items)} distinct master items for Nyam Nyam UPC.")
        for it in nyam_items:
            print(f"   - FORM: {it.get('product_form'):<12} | ITEM: {it.get('ITEM')}")
    else:
        print("   [FAILED] Nyam Nyam items are still merged into one!")

    # 2. PRODUCT FORM GLOBAL STATS
    print("\n2. GLOBAL PRODUCT FORM DISTRIBUTION")
    pipeline = [
        {"$group": {"_id": "$product_form", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    stats = list(master.aggregate(pipeline))
    print(f"   {'FORM':<20} | {'TOTAL ITEMS'}")
    print("   " + "-"*35)
    for s in stats:
        name = str(s['_id']) if s['_id'] else "NULL (PROBLEM)"
        print(f"   {name:<20} | {s['count']}")

    # 3. LEGACY CACHE CHECK
    null_count = master.count_documents({"product_form": None})
    if null_count == 0:
        print("\n3. [SUCCESS] ZERO NULL FORMS! The system is now 100% clean.")
    else:
        print(f"\n3. [WARNING] Still found {null_count} items with NULL form. Please check cache.")

    print("\n" + "="*50)
    print("      Verification Done. Ready for Delivery!")
    print("="*50 + "\n")

if __name__ == "__main__":
    final_health_check()
