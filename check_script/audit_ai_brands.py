from pymongo import MongoClient
import os
from dotenv import load_dotenv

def audit_brands():
    load_dotenv(r'd:\FMCG_Dashboard\backend\.env')
    client = MongoClient(os.getenv('MONGO_URI'))
    db = client['fmcg_mastering']
    collection = db['7-eleven_data']
    
    pipeline = [
        {"$group": {"_id": "$AI_BRAND", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    
    results = list(collection.aggregate(pipeline))
    print("\n--- Top 20 AI Brands in 7-Eleven ---")
    for res in results:
        print(f"{res['_id']}: {res['count']}")
    
    client.close()

if __name__ == "__main__":
    audit_brands()
