from backend.database import get_collection
import re

def clear_targeted_cache():
    cache_coll = get_collection("LLM_CACHE_STORAGE")
    
    # Target patterns for items that were wrongly merged or need re-processing
    targets = [
        "DIP DIP", "BUBBLE PUFF", "HELLO PANDA", "NYAM NYAM",
        "POCKY", "JULIES", "NABATI", "LOACKER", "PEPPERID", 
        "LEXUS", "MUNCHY'S", "HUP SENG", "CREAM-O", "ROMA", 
        "CHEEZA", "BOURBON", "OREO", "KC NBR", "KC QSYB", 
        "BISCO", "NUTELLA", "TOHATO", "KURIYAMA", "APOLLO"
    ]
    
    print("🔍 Searching for targeted cache entries...")
    
    # Using regex to find items containing these keywords
    query = {"item": {"$regex": "|".join(targets), "$options": "i"}}
    
    # Count before deletion
    count = cache_coll.count_documents(query)
    print(f"📦 Found {count} matching entries in cache.")
    
    if count > 0:
        # Fetch names for logging
        docs = list(cache_coll.find(query, {"item": 1}))
        print("\nItems to be cleared:")
        for d in docs[:10]:
            print(f" - {d['item']}")
        if len(docs) > 10:
            print(f" ... and {len(docs) - 10} more.")
            
        # Delete them
        result = cache_coll.delete_many(query)
        print(f"\n✅ Deleted {result.deleted_count} entries from LLM_CACHE_STORAGE.")
    else:
        print("ℹ️ No matching entries found in cache.")

if __name__ == "__main__":
    clear_targeted_cache()
