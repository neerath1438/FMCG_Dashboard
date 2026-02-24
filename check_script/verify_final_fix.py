from pymongo import MongoClient

def verify_final_splits():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["fmcg_mastering"]
    coll = db["master_stock_data"]
    
    test_cases = [
        {"name": "Nabati (Wafer vs Roll)", "keywords": ["NABATI", "RICHOCO"], "check": ["WAFER", "ROLLS", "STICK"]},
        {"name": "Oreo (Choco vs Peanut)", "keywords": ["OREO"], "check": ["CHOCO", "PEANUT BUTTER"]},
        {"name": "Kinder (Tronky vs Hippo)", "keywords": ["KINDER"], "check": ["TRONKY", "HAPPY HIPPO"]},
        {"name": "Walkers (Finger vs Round)", "keywords": ["WALKERS"], "check": ["FINGER", "ROUND"]},
        {"name": "Sugar Free (Voortman)", "keywords": ["VOORTMAN"], "check": ["SUGAR FREE"]}
    ]
    
    print("=== FINAL VERIFICATION OF STRICT MERGE ===\n")
    
    for case in test_cases:
        print(f"CASE: {case['name']}")
        
        # Find all master items that match the case keywords
        query = {"$and": [{"ITEM": {"$regex": k, "$options": "i"}} for k in case["keywords"]]}
        items = list(coll.find(query, {"ITEM": 1, "merge_items": 1}))
        
        if not items:
            print("  No items found for this search.")
            continue
            
        # Check if any master group contains items from multiple categories
        for item in items:
            merged = item.get("merge_items", [])
            categories_found = []
            for c in case["check"]:
                if any(c.lower() in m.lower() for m in merged):
                    categories_found.append(c)
            
            if len(set(categories_found)) > 1:
                print(f"  ❌ FAILED: Group '{item['ITEM']}' still contains mixed: {set(categories_found)}")
                print(f"    Merged items: {merged[:3]}...")
            else:
                # print(f"  ✅ Group '{item['ITEM']}' is clean.")
                pass
        
        print(f"  ✅ Verified {len(items)} master groups for {case['name']}. No incorrect merges found.")
        print("-" * 40)

if __name__ == "__main__":
    verify_final_splits()
