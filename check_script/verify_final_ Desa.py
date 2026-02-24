from pymongo import MongoClient
import os
from dotenv import load_dotenv

def verify_final():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client['fmcg_mastering']
    coll = db['master_stock_data']
    
    items = [
        "DESA ALPHA COOKIES OAT600G",
        "DESA ALPHA COOKIES KOKO KRUNCH 600G",
        "DESA ALPHA BUTTER COOKIES COLORRICE 600G",
        "DESA ALPHA COOKIES CHOCO MELON SEED 600G"
    ]
    
    print(f"{'Original Item Name':<45} | {'Flavour':<15} | {'Size':<10}")
    print("-" * 75)
    
    # Check for direct items or merges
    for it in items:
        # We search in merge_items to find where these items landed
        doc = coll.find_one({"merge_items": it})
        if doc:
            print(f"{it:<45} | {doc.get('flavour'):<15} | {doc.get('size'):<10}")
            if len(doc.get("merge_items", [])) > 1:
                print(f"  ⚠️ ALERT: Still merged with {len(doc['merge_items'])} items")
        else:
            print(f"{it:<45} | NOT FOUND")
    
    client.close()

if __name__ == "__main__":
    verify_final()
