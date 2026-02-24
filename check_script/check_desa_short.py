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
    
    for it in items:
        res = coll.find_one({"item": it})
        if res:
            flv = res['result'].get('flavour')
            print(f"[{it}] -> Flavour: {flv}")
        else:
            print(f"[{it}] -> NOT FOUND")
    
    client.close()

if __name__ == "__main__":
    check()
