from backend.database import get_collection
import re
from difflib import SequenceMatcher

def string_similarity(a, b):
    return SequenceMatcher(None, a.upper(), b.upper()).ratio()

def simple_clean(name):
    if not name: return ""
    # Remove sizes and common noise to check base identity
    s = re.sub(r'\d+\s*(G|GM|K|KG|ML|L)', '', name, flags=re.IGNORECASE)
    words = sorted(list(set(re.findall(r'[A-Z]+', s.upper()))))
    return "".join(words)

def find_manual_entry_errors():
    master_col = get_collection("master_stock_data")
    
    # Filter by LOW CONFIDENCE where typos usually live
    pipeline = [
        {"$match": {"llm_confidence_min": {"$lt": 0.92}}},
        {"$group": {
            "_id": {
                "brand": "$BRAND",
                "market": "$Markets",
                "facts": "$Facts"
            },
            "records": {"$push": {
                "item": "$ITEM",
                "merge_id": "$merge_id"
            }},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    print("🔍 Scanning Master Stock for potential manual entry errors (typos)...")
    results = list(master_col.aggregate(pipeline))
    
    potential_errors = []
    
    for group in results:
        records = group["records"]
        brand = group["_id"]["brand"]
        market = group["_id"]["market"]
        
        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                item1 = records[i]["item"]
                item2 = records[j]["item"]
                
                # Rule 1: String similarity
                sim = string_similarity(item1, item2)
                
                # Rule 2: Cleaned identity similarity
                c1 = simple_clean(item1)
                c2 = simple_clean(item2)
                
                # Target items that are NOT fixed (> 0.70 and <= 0.85)
                # and don't have identical cleaned names (which are already fixed)
                if (0.70 <= sim <= 0.85) and (c1 != c2) and records[i]["merge_id"] != records[j]["merge_id"]:
                    potential_errors.append({
                        "brand": brand,
                        "market": market,
                        "item_a": item1,
                        "item_b": item2,
                        "similarity": round(sim, 2),
                        "reason": f"Needs Manual Review ({round(sim*100)}%)"
                    })

    print(f"\n✅ Found {len(potential_errors)} potential manual entry errors.")
    
    import json
    with open("typo_candidates.json", "w") as f:
        json.dump(potential_errors, f, indent=4)
    print("💾 Results saved to typo_candidates.json")

if __name__ == "__main__":
    find_manual_entry_errors()
