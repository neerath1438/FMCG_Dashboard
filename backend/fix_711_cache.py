import os
from pymongo import MongoClient
from dotenv import load_dotenv
import json
from datetime import datetime

# Import from main triggers FastAPI startup, let's just use the logic directly
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.main import _711_SYSTEM_PROMPT, _call_711_llm

load_dotenv()

def fix_cache():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = client['fmcg_mastering']
    col = db['7-eleven_llm_cache']

    # Keywords that suggest a flavour or variant is missing if result is NONE
    keywords = ["SEAWEED", "SPICY", "KIMCHI", "WASABI", "CHEESE", "SALTED", "ORIGINAL", "POKEMON", "BRICE"]
    
    query = {
        "$or": [
            {"result.7E_flavour": "NONE"},
            {"result.7E_Variant": "NONE"}
        ]
    }
    
    docs = list(col.find(query))
    print(f"Found {len(docs)} candidates with 'NONE' values.")
    
    count = 0
    for doc in docs:
        desc = doc['article_description'].upper()
        should_fix = any(k in desc for k in keywords)
        
        if should_fix:
            print(f"Fixing: {doc['article_description']}")
            new_result = _call_711_llm(doc['article_description'])
            
            col.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "result": new_result,
                    "fixed_at": datetime.utcnow().isoformat()
                }}
            )
            count += 1
            if count % 10 == 0:
                print(f"Progress: {count} fixed...")

    print(f"Finished. Total fixed: {count}")

if __name__ == "__main__":
    fix_cache()
