from pymongo import MongoClient

def clear_cache():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["fmcg_mastering"]
    coll = db["LLM_CACHE_STORAGE"]
    
    keywords = [
        'NABATI', 'OREO', 'GLICO', 'LOTTE', 'KINDER', 'WALKERS', 
        'MARYLAND', 'NABISCO', 'MERBA', 'VOORTMAN', 'ARNOTTS', 
        'VFOODS', 'MEIJI', 'TATAWA', 'REBISCO'
    ]
    
    print(f"Starting cache cleanup for {len(keywords)} brands...")
    total_deleted = 0
    
    for kw in keywords:
        res = coll.delete_many({"item": {"$regex": kw, "$options": "i"}})
        total_deleted += res.deleted_count
        print(f"Keyword '{kw}': Deleted {res.deleted_count} entries")
        
    print(f"\nCleanup finished. Total entries removed: {total_deleted}")

if __name__ == "__main__":
    clear_cache()
