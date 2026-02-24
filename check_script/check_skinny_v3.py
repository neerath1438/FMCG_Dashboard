from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

def run_check():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["fmcg_mastering"]
    col = db["master_stock_data"]
    
    with open("d:/FMCG_Dashboard/final_proof_v3.txt", "w", encoding="utf-8") as f:
        for brand in ["SKINNY BAKER", "OAT KRUNCH"]:
            f.write(f"\n{'='*20} {brand} {'='*20}\n")
            query = {"BRAND": {"$regex": brand, "$options": "i"}}
            docs = list(col.find(query))
            f.write(f"Total Clusters: {len(docs)}\n")
            
            for d in docs:
                items = d.get("merge_items", [])
                if not items: items = [d.get("ITEM")]
                f.write(f"\nID: {d.get('merge_id')} | FLAVOUR: {d.get('flavour')} | VARIANT: {d.get('variant')}\n")
                for item in items:
                    f.write(f"  - {item}\n")

    print("Success: proof written to d:/FMCG_Dashboard/final_proof_v3.txt")
    client.close()

if __name__ == "__main__":
    run_check()
