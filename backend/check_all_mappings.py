from pymongo import MongoClient

def check_all_mappings():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    colls = [c for c in db.list_collection_names() if 'mapping' in c]
    
    print("Mapping Collections Summary (Non-GAP Matches):")
    for c_name in colls:
        col = db[c_name]
        pipeline = [
            {'$match': {'qa_fields.match_level': {'$ne': 'GAP'}}},
            {'$group': {'_id': {'upc': '$UPC', 'item': '$ITEM'}}},
            {'$count': 'count'}
        ]
        res = list(col.aggregate(pipeline))
        count = res[0]['count'] if res else 0
        total = col.count_documents({})
        print(f" - {c_name}: {count} matches (Total: {total})")

if __name__ == "__main__":
    check_all_mappings()
