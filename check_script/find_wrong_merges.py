from pymongo import MongoClient
import json

def find_wrong_merges():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["fmcg_mastering"]
    coll = db["master_stock_data"]

    test_cases = [
        {"name": "GLICO (Petit Q vs Pretz)", "patterns": ["PETIT Q", "PRETZ"]},
        {"name": "LOTTE (Toppo vs Pepero)", "patterns": ["TOPPO", "PEPERO"]},
        {"name": "OREO (Choco vs Peanut)", "patterns": ["CHOCO", "PEANUT BUTTER"]},
        {"name": "KINDER (Tronky vs Hippo)", "patterns": ["TRONKY", "HAPPY HIPPO"]},
        {"name": "WALKERS (Finger vs Round)", "patterns": ["FINGER", "ROUND"]},
        {"name": "NABISCO (Chips Ahoy vs Oreo)", "patterns": ["CHIPS AHOY", "OREO"]},
        {"name": "MERBA (Choc vs Nougat)", "patterns": ["CHOCOLATE COOKIE", "NOUGATELLI"]},
        {"name": "VOORTMAN (Sugar Free)", "patterns": ["SUGAR FREE", "CHOCOLATE CHIP"]},
        {"name": "ARNOTTS (Arrowroot vs Coffee)", "patterns": ["ARROWROOT", "MILK COFFEE"]},
        {"name": "VFOODS (Pineapple vs Donut)", "patterns": ["PINEAPPLE BISCUITS", "MINI DONUT"]},
        {"name": "NABATI (Wafer vs Rolls vs Stick)", "patterns": ["WAFER", "ROLLS", "STICK"]},
        {"name": "TATAWA (Almond vs Hazelnut)", "patterns": ["ALMOND", "HAZELNUT"]}
    ]

    print(f"Searching for wrong merges in {coll.count_documents({})} records...\n")

    for case in test_cases:
        print(f"--- Checking {case['name']} ---")
        
        # Search for items where merge_items contains multiple patterns from the same case
        # This indicates they were merged together
        
        # Build query: merged_from_docs > 1 AND (contains pattern A AND contains pattern B)
        query = {
            "merged_from_docs": {"$gt": 1},
            "$and": [
                {"merge_items": {"$regex": p, "$options": "i"}} for p in case["patterns"]
            ]
        }
        
        matches = list(coll.find(query, {"ITEM": 1, "merge_items": 1, "BRAND": 1, "merged_from_docs": 1}))
        
        if matches:
            for m in matches:
                print(f"FOUND WRONG MERGE!")
                print(f"  Brand: {m.get('BRAND')}")
                print(f"  Master Item: {m.get('ITEM')}")
                print(f"  Original Items in group: {m.get('merge_items')}")
                print("-" * 20)
        else:
            print("  No internal mismatch found for this specific pair in the same group.")
        print()

if __name__ == "__main__":
    find_wrong_merges()
