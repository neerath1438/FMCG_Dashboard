from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

def clear_problematic_cache():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["fmcg_mastering"]
    cache_coll = db["LLM_CACHE_STORAGE"]
    
    # Define keywords for items we want to re-process with new guards
    target_keywords = ["OAT KRUNCH", "SKINNY BAKER", "HELLO PANDA", "YAN YAN", "LUCKY STICK"]
    
    deleted_count = 0
    for kw in target_keywords:
        res = cache_coll.delete_many({"item": {"$regex": kw, "$options": "i"}})
        deleted_count += res.deleted_count
        print(f"Deleted {res.deleted_count} cache entries for: {kw}")
    
    print(f"Total cache items cleared: {deleted_count}")
    client.close()

if __name__ == "__main__":
    clear_problematic_cache()
