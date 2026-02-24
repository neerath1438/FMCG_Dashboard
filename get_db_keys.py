from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017")
db = client["fmcg_mastering"]

def get_keys(collection_name):
    doc = db[collection_name].find_one()
    if doc:
        keys = sorted(list(doc.keys()))
        print(f"--- Keys for {collection_name} ---")
        for k in keys:
            val = doc[k]
            vtype = type(val).__name__
            # Print field name, type, and a snippet of the value
            snippet = str(val)[:50] if val is not None else "None"
            print(f"{k} ({vtype}): {snippet}")

get_keys("7-eleven_data")
get_keys("master_stock_data")
