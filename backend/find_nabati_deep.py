
from pymongo import MongoClient

def find_nabati():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    terms = ['NABATI', 'RICHEESE', 'NEXTAR']
    
    for coll_name in db.list_collection_names():
        print(f"\nChecking collection: {coll_name}")
        for term in terms:
            count = db[coll_name].count_documents({'ITEM': {'$regex': term, '$options': 'i'}})
            if count > 0:
                print(f"  Found {count} items for '{term}'")
                # Show some samples
                samples = list(db[coll_name].find({'ITEM': {'$regex': term, '$options': 'i'}}, {'ITEM': 1}).limit(5))
                for s in samples:
                    print(f"    - {s['ITEM']}")

if __name__ == "__main__":
    find_nabati()
