from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

def final_verification():
    print("=== FINAL GLOBAL BRAND VERIFICATION ===")
    
    # Identify top 20 most merged items across all brands
    pipeline = [
        {"$sort": {"merged_from_docs": -1}},
        {"$limit": 20},
        {"$project": {
            "BRAND": 1,
            "ITEM": 1,
            "product_form": 1,
            "merged_from_docs": 1,
            "UPC": 1
        }}
    ]
    
    top_merges = list(master.aggregate(pipeline))
    print("\nTop 20 Merged Items (High Merge Density):")
    print(f"{'BRAND':<15} | {'FORM':<12} | {'COUNT':<5} | {'ITEM'}")
    print("-" * 80)
    for m in top_merges:
        brand = str(m.get('BRAND'))[:15]
        form = str(m.get('product_form'))[:12]
        count = m.get('merged_from_docs')
        item = str(m.get('ITEM'))[:40]
        print(f"{brand:<15} | {form:<12} | {count:<5} | {item}")

    # Check for items that HAVE a UPC but NO product_form (legacy cache check)
    missing_form_count = master.count_documents({"product_form": None})
    print(f"\nItems still missing product_form: {missing_form_count}")
    
    if missing_form_count > 0:
        print("\nTop brands with missing product_form (Legacy Cache):")
        pipeline_missing = [
            {"$match": {"product_form": None}},
            {"$group": {"_id": "$BRAND", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        missing_brands = list(master.aggregate(pipeline_missing))
        for mb in missing_brands:
            print(f"  - {mb['_id']}: {mb['count']} items")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    final_verification()
