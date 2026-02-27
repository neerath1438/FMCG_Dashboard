from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['fmcg_mastering']
coll_results = db['mapping_results']

counts = list(coll_results.aggregate([{'$group': {'_id': '$Match_Level', 'count': {'$sum': 1}}}]))
if not counts:
    print("Collection is empty!")
else:
    for c in counts:
        print(f"{c['_id']}: {c['count']}")

sources = list(coll_results.aggregate([{'$group': {'_id': '$Source', 'count': {'$sum': 1}}}]))
print("\nSources:")
for s in sources:
    print(f"{s['_id']}: {s['count']}")
