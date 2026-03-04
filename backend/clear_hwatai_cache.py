
from pymongo import MongoClient

def clear_hwatai_cache():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    cache_coll = db['LLM_CACHE_STORAGE']
    
    targets = [
        "HWA TAI GOLDEN ASST 505G",
        "HWA TAI GOLDEN ASSTORTED 505G",
        "HWA TAI LUXURY VEGETABLE CRACKERS 18.5GM X 12(222GM)",
        "LUXURY CRACKER VEGETABLE 222GM(18.5GM X 12)"
    ]
    
    print(f"--- Selective Cache Clear (Hwa Tai) ---")
    for item in targets:
        res = cache_coll.delete_many({"item": {"$regex": item, "$options": "i"}})
        print(f"Deleted {res.deleted_count} cache entries for: {item}")

if __name__ == "__main__":
    clear_hwatai_cache()
