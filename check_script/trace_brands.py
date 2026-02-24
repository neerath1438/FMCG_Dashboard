from pymongo import MongoClient
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
raw = db["raw_data"]
master = db["master_stock_data"]

missing_brands = ['EXCLUSIVE BRAND', 'MASUYA', 'PRIVATE LABEL', 'SNAZK']

with open("d:/FMCG_Dashboard/brand_trace.txt", "w") as f:
    for rb in missing_brands:
        r_doc = raw.find_one({"BRAND": rb})
        if r_doc:
            item = r_doc.get("ITEM")
            upc = r_doc.get("UPC")
            m_doc = master.find_one({"$or": [{"UPC": upc}, {"ITEM": item}, {"MERGE_ITEMS": {"$regex": re.escape(item) if item else "XXXXX"}}]})
            if m_doc:
                f.write(f"{rb} -> {m_doc.get('BRAND')}\n")
            else:
                f.write(f"{rb} -> NOT FOUND\n")
