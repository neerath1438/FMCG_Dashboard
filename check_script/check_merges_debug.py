import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

def check_merges():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    target_items = [
        "MILCH KNOPPERS WAFER 25GM",
        "GLICO PETIT Q BISCUIT 30G",
        "LOTTE KOALA`S MARCH 4X15G",
        "MCVITIES MILK CHOCOLATE DIGESTVS 200G",
        "MCVITIE'S DARKCHO DIGESTV BISC 200GM",
        "GLICO BRAND POCKY STRAWBERRY 38GM",
        "LOTUS BISOFF & GO 45G"
    ]
    
    single_stock_coll = db["single_stock_data"]
    
    # Try both casings just to be safe
    queries = [
        {"FACTS": {"$regex": "^Sales Value", "$options": "i"}, "MARKETS": {"$regex": "^Pen Malaysia", "$options": "i"}},
        {"Facts": {"$regex": "^Sales Value", "$options": "i"}, "Markets": {"$regex": "^Pen Malaysia", "$options": "i"}}
    ]
    
    print("Checking if items exist in single_stock_data...")
    for item in target_items:
        found = False
        for query in queries:
            # Check primary
            doc = single_stock_coll.find_one({"ITEM": item, **query})
            if doc:
                print(f"FOUND (Primary): {item}")
                found = True
                break
            
            # Check merged
            merged_doc = single_stock_coll.find_one({"merge_items": item, **query})
            if merged_doc:
                print(f"FOUND (Merged into {merged_doc['ITEM']}): {item}")
                found = True
                break
        
        if not found:
            print(f"NOT FOUND: {item}")

if __name__ == "__main__":
    check_merges()
