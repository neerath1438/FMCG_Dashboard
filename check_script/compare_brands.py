from pymongo import MongoClient
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]

raw_coll = db["raw_data"]
master_coll = db["master_stock_data"]

# Get unique brands
raw_brands = set([str(b).strip() for b in raw_coll.distinct("BRAND") if b and str(b).strip()])
master_brands = set([str(b).strip() for b in master_coll.distinct("BRAND") if b and str(b).strip()])

print(f"RAW: {len(raw_brands)}, MASTER: {len(master_brands)}")

missing = sorted(list(raw_brands - master_brands))
for rb in missing:
    doc = raw_coll.find_one({"BRAND": rb})
    if doc:
        item = str(doc.get("ITEM", ""))
        upc = doc.get("UPC")
        m_doc = master_coll.find_one({"$or": [{"UPC": upc}, {"ITEM": item}, {"MERGE_ITEMS": {"$regex": re.escape(item) if item else "XXXXXX"}}]})
        master_brand = m_doc.get('BRAND') if m_doc else "NOT FOUND"
        print(f"DEBUG_RES: {rb} >>> {master_brand}")
