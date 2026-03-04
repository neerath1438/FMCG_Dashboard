
from pymongo import MongoClient

def clear_pocky_cache():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    cache_coll = db['LLM_CACHE_STORAGE']
    
    targets = [
        "GLICO POCKY BISC FAMILY P CHCLTE 176GM",
        "POCKY FAMILY PACK CHOCOLATE 176G"
    ]
    
    print(f"--- Selective Cache Clear (Pocky) ---")
    for item in targets:
        # Match using regex to handle varying context-aware names
        res = cache_coll.delete_many({"item": {"$regex": item, "$options": "i"}})
        print(f"Deleted {res.deleted_count} cache entries for: {item}")

if __name__ == "__main__":
    clear_pocky_cache()
