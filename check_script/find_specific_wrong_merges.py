from pymongo import MongoClient
import pandas as pd

def find_specific_wrong_merges():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["fmcg_mastering"]
    coll = db["master_stock_data"]

    wrong_groups = []

    # 1. Nabati Richoco (Rolls vs Wafer vs Stick)
    nabati = list(coll.find({
        "BRAND": "NABATI",
        "merged_from_docs": {"$gt": 1},
        "merge_items": {"$regex": "ROLLS", "$options": "i"},
        "$or": [
            {"merge_items": {"$regex": "WAFER", "$options": "i"}},
            {"merge_items": {"$regex": "STICK", "$options": "i"}}
        ]
    }))
    wrong_groups.extend(nabati)

    # 2. Oreo (Choco vs Peanut Butter)
    oreo = list(coll.find({
        "BRAND": "OREO",
        "merged_from_docs": {"$gt": 1},
        "merge_items": {"$regex": "PEANUT BUTTER", "$options": "i"}
    }))
    wrong_groups.extend(oreo)

    # 3. Glico (Petit Q vs Pretz)
    glico = list(coll.find({
        "BRAND": "GLICO",
        "merged_from_docs": {"$gt": 1},
        "merge_items": {"$regex": "PETIT Q", "$options": "i"}
    }))
    wrong_groups.extend(glico)

    # 4. Nabisco (Chips Ahoy vs Oreo)
    nabisco = list(coll.find({
        "merged_from_docs": {"$gt": 1},
        "merge_items": {"$regex": "CHIPS AHOY", "$options": "i"},
        "merge_items": {"$regex": "OREO", "$options": "i"}
    }))
    wrong_groups.extend(nabisco)

    # 5. Maryland (Flavour variations)
    maryland = list(coll.find({
        "BRAND": "MARYLAND",
        "merged_from_docs": {"$gt": 1}
    }))
    wrong_groups.extend(maryland)

    # 6. Walkers (Finger vs Rounds)
    walkers = list(coll.find({
        "BRAND": "WALKERS",
        "merged_from_docs": {"$gt": 1},
        "merge_items": {"$regex": "FINGER", "$options": "i"}
    }))
    wrong_groups.extend(walkers)

    if not wrong_groups:
        print("No specific wrong merges found using these filters. Trying broad search...")
        # Broad search for ANY merge items containing mixed keywords for the brands
        all_merged = list(coll.find({"merged_from_docs": {"$gt": 1}}, {"ITEM": 1, "merge_items": 1, "BRAND": 1}))
        print(f"Total merged master records: {len(all_merged)}")
        return

    # Remove duplicates from our list
    unique_ids = set()
    final_list = []
    for g in wrong_groups:
        if str(g["merge_id"]) not in unique_ids:
            unique_ids.add(str(g["merge_id"]))
            final_list.append(g)

    print(f"Found {len(final_list)} suspicious master groups.\n")
    for g in final_list:
        print(f"BRAND: {g.get('BRAND')}")
        print(f"MASTER ITEM: {g.get('ITEM')}")
        print(f"MERGED ITEMS: {g.get('merge_items')}")
        print("-" * 30)

if __name__ == "__main__":
    find_specific_wrong_merges()
