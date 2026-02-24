from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]

# Aggregate to find UPCs that have multiple different product_form values
pipeline = [
    {"$match": {"product_form": {"$ne": None}}},
    {"$group": {
        "_id": "$UPC",
        "forms": {"$addToSet": "$product_form"},
        "brands": {"$addToSet": "$BRAND"},
        "count": {"$sum": 1}
    }},
    {"$match": {"$expr": {"$gt": [{"$size": "$forms"}, 1]}}}
]

print("=== UPCs with Multiple Product Forms ===")
results = list(db.master_stock_data.aggregate(pipeline))
print(f"Total UPCs with different forms: {len(results)}")

for res in results[:20]:
    print(f"UPC: {res['_id']} | Brands: {res['brands']} | Forms: {res['forms']}")

print("\n=== Verification Finished ===")
