import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = client['fmcg_mastering']
    return db['7-eleven_data'], db['master_stock_data']

def analyze_pocky():
    coll_7e, coll_master = connect_db()
    
    print("\n--- 7-Eleven Pocky Examples ---")
    items_7e = list(coll_7e.find({"ArticleDescription": {"$regex": "Pocky", "$options": "i"}}).limit(10))
    for d in items_7e:
        print(f"Desc: {d['ArticleDescription']}")
        print(f"  7E_Brand: {d.get('7E_Brand')}, 7E_Variant: {d.get('7E_Variant')}, 7E_flavour: {d.get('7E_flavour')}, Size: {d.get('7E_Size')}")
        print("-" * 30)

    print("\n--- Nielsen Pocky Examples ---")
    items_n = list(coll_master.find({"ITEM": {"$regex": "Pocky", "$options": "i"}}).limit(10))
    for m in items_n:
        print(f"Item: {m['ITEM']}")
        print(f"  BRAND: {m.get('BRAND')}, VARIANT: {m.get('VARIANT')}, flavour: {m.get('flavour')}, Size: {m.get('NRMSIZE')}")
        print("-" * 30)

if __name__ == "__main__":
    analyze_pocky()
