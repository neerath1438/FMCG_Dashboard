from pymongo import MongoClient
import os
from dotenv import load_dotenv

def audit_merged_items():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client['fmcg_mastering']
    coll = db['master_stock_data']
    
    query = { "$expr": { "$gt": [{ "$size": "$merge_items" }, 1] } }
    cursor = coll.find(query, {"merge_items": 1, "merged_upcs": 1, "_id": 0})
    
    merged_groups = list(cursor)
    print(f"Total merged groups found: {len(merged_groups)}")
    
    with open("audit_merged_results.txt", "w", encoding="utf-8") as f:
        for i, group in enumerate(merged_groups):
            items = group.get("merge_items", [])
            f.write(f"Group {i+1}:\n")
            for it in items:
                f.write(f"  - {it}\n")
            f.write("-" * 40 + "\n")
            
            if i < 5: # Print some to console for quick look
                print(f"Group {i+1}: {items}")

    print("\nFull results saved to audit_merged_results.txt")
    client.close()

if __name__ == "__main__":
    audit_merged_items()
