from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

def verify():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["fmcg_mastering"]
    
    target_upcs = [
        "200172907644", "200172963163", "5098532321071", # Skinny Baker
        "9556439885158", "9556439890763", "9556439890800"  # Oat Krunch
    ]
    
    # We check master_stock_data to see which cluster these UPCs belong to
    print(f"Verifying targeted UPCs in master_stock_data...\n")
    for upc in target_upcs:
        # Search in merged_upcs array
        master = db["master_stock_data"].find_one({"merged_upcs": upc})
        if master:
            print(f"UPC: {upc}")
            print(f"  Item: {master.get('ITEM')}")
            print(f"  Flavour: {master.get('flavour')}")
            print(f"  Variant: {master.get('variant')}")
            print(f"  Merged from {master.get('merged_from_docs')} records")
        else:
            print(f"UPC: {upc} - NOT FOUND in any master cluster")
        print("-" * 20)

if __name__ == "__main__":
    verify()
