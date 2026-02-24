from pymongo import MongoClient
import os
from dotenv import load_dotenv

def check_match_levels():
    load_dotenv(r'd:\FMCG_Dashboard\backend\.env')
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri)
    db = client["fmcg_mastering"]
    collection = db["7eleven_extra_items"]
    
    pipeline = [
        {"$group": {"_id": "$Match_Level", "count": {"$sum": 1}}}
    ]
    
    results = list(collection.aggregate(pipeline))
    
    print("\n--- Match Level Stats (MongoDB) ---")
    for res in results:
        print(f"{res['_id']}: {res['count']}")
    
    client.close()

if __name__ == "__main__":
    check_match_levels()
