
from pymongo import MongoClient

def clear_specific_cache():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    cache_coll = db['LLM_CACHE_STORAGE']
    
    # Target items reported by user
    # Note: cache stores the "context-aware" item name used during LLM call
    targets = [
        "BOURBON PETIT USUYAKI 33GM",
        "BOURBON PETIT EBI 33GM"
    ]
    
    print(f"--- Selective Cache Clear ---")
    for item in targets:
        # Standardize matching to how processor.py lookups work
        # Sometimes brand is prepended in context, so we check both
        res = cache_coll.delete_many({"item": {"$regex": item, "$options": "i"}})
        print(f"Deleted {res.deleted_count} cache entries for: {item}")

if __name__ == "__main__":
    clear_specific_cache()
