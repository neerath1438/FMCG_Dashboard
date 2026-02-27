
import sys
import os
from pymongo import MongoClient

def search_patterns():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    patterns = ['468', '123.5', '20.4', 'WAFER ROLL', 'RED VELVET', 'MINI']
    colls = ['single_stock_data', 'raw_data', 'master_stock_data']
    
    print("--- PATTERN SEARCH ---")
    for coll_name in colls:
        coll = db[coll_name]
        print(f"\nCollection: {coll_name}")
        for p in patterns:
            results = list(coll.find({"ITEM": {"$regex": p, "$options": "i"}}, {"ITEM": 1}).limit(10))
            if results:
                print(f"  P: {p} -> {results}")

if __name__ == "__main__":
    search_patterns()
