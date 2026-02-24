from pymongo import MongoClient
import os
from dotenv import load_dotenv

def check_updates():
    load_dotenv(r"backend\.env")
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client['fmcg_mastering']
    coll = db['LLM_CACHE_STORAGE']
    
    keywords = ["OATKRUNCH", "POCKY", "CHUNKY", "ORGANIC", "GOKUBOSO"]
    
    print(f"{'Item Name':<60} | {'Flavour':<15} | {'Variant':<15}")
    print("-" * 95)
    
    for kw in keywords:
        cursor = coll.find({"item": {"$regex": kw, "$options": "i"}})
        for doc in cursor:
            res = doc.get("result", {})
            print(f"{doc['item'][:60]:<60} | {res.get('flavour'):<15} | {res.get('variant'):<15}")
            
    client.close()

if __name__ == "__main__":
    check_updates()
