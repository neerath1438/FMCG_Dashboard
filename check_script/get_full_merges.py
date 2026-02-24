from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

def audit_merges():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["fmcg_mastering"]
    
    # User's specific query
    cursor = db.master_stock_data.find({
        "Facts": "Sales Value",
        "Markets": "Pen Malaysia",
        "$expr": { "$gt": [{ "$size": "$merge_items" }, 1] }
    })
    
    results = list(cursor)
    print(f"Total merged items found: {len(results)}")
    
    with open("audit_full_merges.json", "w") as f:
        # Save simplified version for easier inspection
        simplified = []
        for r in results:
            simplified.append({
                "ITEM": r.get("ITEM"),
                "merge_items": r.get("merge_items"),
                "flavour": r.get("flavour"),
                "variant": r.get("variant"),
                "size": r.get("size")
            })
        json.dump(simplified, f, indent=2)

if __name__ == "__main__":
    audit_merges()
