from pymongo import MongoClient
import os
from dotenv import load_dotenv

def check():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client['fmcg_mastering']
    coll = db['LLM_CACHE_STORAGE']
    
    items = [
        "DESA ALPHA COOKIES OAT600G",
        "DESA ALPHA COOKIES KOKO KRUNCH 600G",
        "DESA ALPHA BUTTER COOKIES COLORRICE 600G",
        "DESA ALPHA COOKIES CHOCO MELON SEED 600G"
    ]
    
    with open("desa_final_check.txt", "w", encoding="utf-8") as f:
        for it in items:
            res = coll.find_one({"item": it})
            flv = res['result'].get('flavour') if res else "NOT FOUND"
            f.write(f"[{it}] -> Flavour: {flv}\n")
    
    client.close()

if __name__ == "__main__":
    check()
