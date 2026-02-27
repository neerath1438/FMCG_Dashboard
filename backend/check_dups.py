from pymongo import MongoClient

def check_dups():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    col = db['7-eleven_llm_cache']
    
    pipeline = [
        {'$group': {'_id': '$article_description', 'count': {'$sum': 1}}},
        {'$match': {'count': {'$gt': 1}}}
    ]
    dups = list(col.aggregate(pipeline))
    print(f"Total Duplicate Groups: {len(dups)}")
    for d in dups[:10]:
        print(d)

    # Also check for weird characters
    print("\nSample article descriptions:")
    for doc in col.find().limit(5):
        print(f"[{doc['article_description']}]")

if __name__ == "__main__":
    check_dups()
