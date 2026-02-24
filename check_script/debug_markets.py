
from backend.database import get_collection
import json

def debug_markets():
    try:
        coll = get_collection("MASTER_STOCK")
        
        # 1. Total Count
        count = coll.count_documents({})
        
        # 2. Distinct Markets
        markets = coll.distinct("Markets")
        
        with open("debug_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Total Documents: {count}\n\n")
            
            f.write("--- Distinct Markets Found ---\n")
            for m in markets:
                f.write(f"'{m}'\n")
                
            f.write("\n--- Testing Query 'EM' ---\n")
            res_em = list(coll.find({"Markets": {"$regex": "EM", "$options": "i"}}).limit(5))
            f.write(f"Docs found matching 'EM': {len(res_em)}\n")
            for r in res_em:
                 f.write(f"  - {r.get('ITEM')} ({r.get('Markets')})\n")
            
            f.write("\n--- Testing Query 'East Malaysia' ---\n")
            res_full = list(coll.find({"Markets": {"$regex": "East Malaysia", "$options": "i"}}).limit(5))
            f.write(f"Docs found matching 'East Malaysia': {len(res_full)}\n")
            for r in res_full:
                 f.write(f"  - {r.get('ITEM')} ({r.get('Markets')})\n")
                 
        print("Debug written to debug_output.txt")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_markets()
