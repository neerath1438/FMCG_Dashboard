
from pymongo import MongoClient

def check_db():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    for coll_name in db.list_collection_names():
        count = db[coll_name].count_documents({})
        print(f"{coll_name}: {count}")

if __name__ == "__main__":
    check_db()
