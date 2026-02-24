from pymongo import MongoClient
import os
import re
from dotenv import load_dotenv

def normalize_synonyms(text):
    if not text: return ""
    s = str(text).upper()
    syns = {
        "CHOCOLATE": ["COCOA", "CHOC", "CHOCO", "COK"],
        "GRAM": ["GM", "GMS", "G"],
        "BISCUIT": ["BISCUITS", "COOKIES", "COOKIE", "SNACK", "SNACKS", "STICK", "STICKS", "STIX"],
    }
    for primary, aliases in syns.items():
        for alias in aliases:
            s = re.sub(rf'\b{alias}\b', primary, s)
    return s

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
        clean = normalize_synonyms(it)
        print(f"Item: {it}")
        print(f"  Cleaned: {clean}")
        if res:
            print(f"  Current Flavour: {res['result'].get('flavour')}")
        else:
            print("  NOT FOUND")
        print("-" * 20)
    
    client.close()

if __name__ == "__main__":
    check()
