
from pymongo import MongoClient

def clear_langue_de_chat_cache():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    cache_coll = db['LLM_CACHE_STORAGE']
    
    targets = [
        "BOURBON PETIT LANGUE DE CHA CHCLTE 47G",
        "BOURBON PETIT LANGUE DE CH WCHCLTE 47G"
    ]
    
    print(f"--- Selective Cache Clear (Langue de Chat) ---")
    for item in targets:
        res = cache_coll.delete_many({"item": {"$regex": item, "$options": "i"}})
        print(f"Deleted {res.deleted_count} cache entries for: {item}")

if __name__ == "__main__":
    clear_langue_de_chat_cache()
