
from pymongo import MongoClient

def clear_lexus_cookies_cache():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    cache_coll = db['LLM_CACHE_STORAGE']
    
    targets = [
        "LEXUS ORIGINAL CHOCOLATE CHIP COOKIES 189GM",
        "LEXUS MIXED NUTS CHOCOLATE CHIP COOKIES 189GM"
    ]
    
    print(f"--- Selective Cache Clear (Lexus Cookies) ---")
    for item in targets:
        res = cache_coll.delete_many({"item": {"$regex": item, "$options": "i"}})
        print(f"Deleted {res.deleted_count} cache entries for: {item}")

if __name__ == "__main__":
    clear_lexus_cookies_cache()
