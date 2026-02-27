from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def sync_data():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = client['fmcg_mastering']
    data_col = db['7-eleven_data']
    cache_col = db['7-eleven_llm_cache']
    
    print("Starting sync: 7-eleven_data <-- 7-eleven_llm_cache")
    
    # Get all unique article descriptions in 7-eleven_data
    unique_descs = data_col.distinct("ArticleDescription")
    print(f"Found {len(unique_descs)} unique descriptions in 7-eleven_data.")
    
    count = 0
    updated = 0
    for desc in unique_descs:
        cache_doc = cache_col.find_one({"article_description": desc})
        if cache_doc and "result" in cache_doc:
            res = cache_doc["result"]
            
            # Update all documents in data_col with this description
            result = data_col.update_many(
                {"ArticleDescription": desc},
                {"$set": {
                    "ArticleDescription_clean": res.get("ArticleDescription_clean"),
                    "7E_Nrmsize": res.get("7E_Nrmsize"),
                    "7E_MPack": res.get("7E_MPack"),
                    "7E_Variant": res.get("7E_Variant"),
                    "7E_product_form": res.get("7E_product_form"),
                    "7E_flavour": res.get("7E_flavour"),
                    "synced_at": cache_doc.get("fixed_at") or cache_doc.get("cached_at")
                }}
            )
            if result.modified_count > 0:
                updated += 1
            
        count += 1
        if count % 100 == 0:
            print(f"Processed {count}/{len(unique_descs)} descriptions...")

    print(f"Sync complete. {updated} unique descriptions (impacting many rows) updated.")

if __name__ == "__main__":
    sync_data()
