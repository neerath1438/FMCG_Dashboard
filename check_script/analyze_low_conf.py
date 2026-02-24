from backend.database import get_collection
import re

def simple_clean_item(name):
    if not name: return ""
    s = str(name).upper()
    for word in ["ITEM", "PACK", "FLAVOUR", "FLV"]:
        s = s.replace(word, " ")
    words = sorted(list(set(re.findall(r'[A-Z0-9]+', s))))
    return "".join(words)

def analyze_low_conf_candidates():
    master_col = get_collection("master_stock_data")
    
    # We want to find items that have the same BRAND + MARKET + MPACK + FACTS 
    # but different merge_ids (meaning they are separate records)
    # and check if their ITEM names are logically the same.
    
    pipeline = [
        {"$group": {
            "_id": {
                "brand": "$BRAND",
                "market": "$Markets",
                "mpack": "$MPACK",
                "facts": "$Facts"
            },
            "records": {"$push": {
                "item": "$ITEM",
                "merge_id": "$merge_id",
                "norm_item": "$normalized_item"
            }},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    print("🔍 Analyzing potential merge candidates in Master Stock...")
    results = list(master_col.aggregate(pipeline))
    
    matches_to_report = []
    
    for group in results:
        records = group["records"]
        # Check if items within this Brand/Market/Pack/Facts bucket are "similar"
        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                item1 = records[i]["item"]
                item2 = records[j]["item"]
                
                # Check if they are basically the same after cleaning
                c1 = simple_clean_item(item1)
                c2 = simple_clean_item(item2)
                
                # If they are very similar but in different records
                if c1 == c2:
                    matches_to_report.append({
                        "brand": group["_id"]["brand"],
                        "market": group["_id"]["market"],
                        "items": [item1, item2],
                        "reason": "Identical clean names"
                    })
                elif len(set(re.findall(r'[A-Z]+', item1.upper())) & set(re.findall(r'[A-Z]+', item2.upper()))) > 2:
                    # Just for manual review: share more than 2 words
                    matches_to_report.append({
                        "brand": group["_id"]["brand"],
                        "market": group["_id"]["market"],
                        "items": [item1, item2],
                        "reason": "Shared words (Manual Review)"
                    })

    # Display top 15 interesting cases
    print(f"\nFound {len(matches_to_report)} potential candidates for merging.")
    print("-" * 50)
    for m in matches_to_report[:20]:
        print(f"Brand: {m['brand']} | Market: {m['market']}")
        print(f"  Item A: {m['items'][0]}")
        print(f"  Item B: {m['items'][1]}")
        print(f"  Reason: {m['reason']}")
        print("-" * 30)

if __name__ == "__main__":
    analyze_low_conf_candidates()
