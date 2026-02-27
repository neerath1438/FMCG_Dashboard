from pymongo import MongoClient

db = MongoClient('mongodb://localhost:27017')['fmcg_mastering']
items = [
    "Julie's Cocoro Chocolate Wafer Rolls 100g",
    "Julie's One Bite's Chocolate 85g",
    "Julie's One Bite's Peanut Butter 73g",
    "Julie's Butter Crackers 135g"
]

print("--- VERIFICATION RESULTS ---")
for item in items:
    found = db['mapping_results'].find_one({'ArticleDescription': item})
    if found:
        print(f"Desc: {found.get('ArticleDescription')}")
        print(f"  Level: {found.get('Match_Level')} | Matched: {found.get('Matched_ITEM')}")
    else:
        print(f"Not found in results: {item}")
