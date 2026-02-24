from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

def verify_final():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["fmcg_mastering"]
    master_coll = db["master_stock_data"]
    
    brands = ["OAT KRUNCH", "THE SKINNY BAKER"]
    
    print("Verifying targeted splits...")
    for brand in brands:
        print(f"\n--- Brand: {brand} ---")
        # Find all master records for this brand
        docs = list(master_coll.find({"BRAND": {"$regex": brand, "$options": "i"}}))
        print(f"Found {len(docs)} master records.")
        
        for doc in docs:
            items = doc.get("merge_items", [doc.get("ITEM")])
            flavour = doc.get("flavour", "NONE")
            variant = doc.get("variant", "NONE")
            merge_id = doc.get("merge_id")
            
            print(f"[Cluster {merge_id}] Flavour: {flavour} | Variant: {variant}")
            for item in items:
                print(f"  - {item}")
    
    client.close()

if __name__ == "__main__":
    verify_final()
