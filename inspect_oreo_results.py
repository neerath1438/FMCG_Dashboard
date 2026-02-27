from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['fmcg_mastering']
coll_results = db['mapping_results']

print(f"{'Article Description':<45} | {'Match Level':<12} | {'Matched Item':<45}")
print("-" * 110)

oreo_results = list(coll_results.find({"7E_Brand": {"$regex": "OREO", "$options": "i"}, "Source": "7-Eleven"}))

for r in oreo_results:
    desc = r.get('ArticleDescription', 'N/A')
    level = r.get('Match_Level', 'N/A')
    matched = r.get('Matched_ITEM', 'N/A') or 'GAP'
    print(f"{desc[:45]:<45} | {level:<12} | {matched[:45]:<45}")

print(f"\nTotal OREO items found in results: {len(oreo_results)}")
