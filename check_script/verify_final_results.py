from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

print("\n=== FINAL VERIFICATION RESULTS ===")

# 1. Nyam Nyam Check
print("\n[NYAM NYAM CHECK]")
nyam = list(master.find({"UPC": 8886015402037}))
print(f"Total Master Items for UPC 8886015402037: {len(nyam)}")
for it in nyam:
    print(f" - Form: {it.get('product_form')} | Item: {it.get('ITEM')}")

# 2. Null Form Check
print("\n[NULL FORM CHECK]")
null_count = master.count_documents({"product_form": None})
print(f"Items with product_form = NULL: {null_count}")

# 3. Form Distribution
print("\n[FORM DISTRIBUTION]")
pipeline = [
    {"$group": {"_id": "$product_form", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 10}
]
for s in master.aggregate(pipeline):
    print(f" - {s['_id']}: {s['count']}")

print("\n=== VERIFICATION COMPLETE ===")
