from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

def run_check():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["fmcg_mastering"]
    col = db["master_stock_data"]
    
    print("\nVERIFYING OAT KRUNCH CLUSTERS:")
    query = {"BRAND": {"$regex": "OAT KRUNCH", "$options": "i"}}
    docs = list(col.find(query))
    print(f"Total Clusters for Oat Krunch: {len(docs)}")
    
    for d in docs:
        items = d.get("merge_items", [])
        if not items: items = [d.get("ITEM")]
        print(f"\nID: {d.get('merge_id')} | FLAVOUR: {d.get('flavour')}")
        for item in items[:3]:
            print(f"  - {item}")
        if len(items) > 3:
            print(f"  - ... and {len(items)-3} more")

    print("\nVERIFYING SKINNY BAKER CLUSTERS:")
    query = {"BRAND": {"$regex": "SKINNY BAKER", "$options": "i"}}
    docs = list(col.find(query))
    print(f"Total Clusters for Skinny Baker: {len(docs)}")
    for d in docs:
        print(f"ID: {d.get('merge_id')} | FLAVOUR: {d.get('flavour')} | Items: {len(d.get('merge_items', []))}")

    # Write to a file as well
    with open("final_proof_v2.txt", "w") as f:
        f.write("OAT KRUNCH CLUSTERS:\n")
        query = {"BRAND": {"$regex": "OAT KRUNCH", "$options": "i"}}
        docs = list(col.find(query))
        for d in docs:
            f.write(f"ID: {d.get('merge_id')} | FLAVOUR: {d.get('flavour')}\n")
            for item in d.get('merge_items', [])[:3]:
                f.write(f"  - {item}\n")
        
        f.write("\nSKINNY BAKER CLUSTERS:\n")
        query = {"BRAND": {"$regex": "SKINNY BAKER", "$options": "i"}}
        docs = list(col.find(query))
        for d in docs:
            f.write(f"ID: {d.get('merge_id')} | FLAVOUR: {d.get('flavour')}\n")

    client.close()

if __name__ == "__main__":
    run_check()
