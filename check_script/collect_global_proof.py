from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]

# Find a few UPCs that split successfully into different forms
pipeline = [
    {"$group": {
        "_id": "$UPC",
        "distinct_forms": {"$addToSet": "$product_form"},
        "count": {"$sum": 1}
    }},
    {"$match": {"$expr": {"$gt": [{"$size": "$distinct_forms"}, 1]}}}
]

splits = list(db.master_stock_data.aggregate(pipeline))
print(f"Total UPCs that split into different forms: {len(splits)}")

for s in splits[:5]:
    upc = s['_id']
    items = list(db.master_stock_data.find({"UPC": upc}, {"ITEM": 1, "product_form": 1, "BRAND": 1}))
    print(f"\nUPC: {upc}")
    for it in items:
        print(f"  [{it.get('BRAND')}] {it.get('ITEM')} -> FORM: {it.get('product_form')}")
