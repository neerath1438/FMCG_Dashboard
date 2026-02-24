from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

def verify_cache():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["fmcg_mastering"]
    cache = db["LLM_CACHE_STORAGE"]
    
    test_items = [
        "MUNCHYS OATKRUNCH S/BERRY&B/CURR 390G(15X26GM)",
        "MUNCHYS OATKRUNCH NUTTY CHOCO 390G(15X26GM)",
        "SKINNY BAKERS SALTED CRMEL CHOC CHIP COOKIES 150G",
        "SKINNY BAKERS CRNBERIES WHITE CHOC CHIP CKS 150G"
    ]
    
    print("Verifying Cache for problematic items:\n")
    for item in test_items:
        res = cache.find_one({"item": item})
        if res:
            data = res.get("result", {})
            print(f"Item: {item}")
            print(f"  Brand: {data.get('brand')}")
            print(f"  Flavour: {data.get('flavour')}")
            print(f"  Variant: {data.get('variant')}")
        else:
            print(f"Item: {item} - NOT FOUND IN CACHE")
        print("-" * 30)

if __name__ == "__main__":
    verify_cache()
