from pymongo import MongoClient
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
raw = db["raw_data"]
master = db["master_stock_data"]

# Trace by UPC
upcs = ["9555480009087"] # From EXCLUSIVE BRAND
for upc in upcs:
    r_doc = raw.find_one({"UPC": upc})
    m_doc = master.find_one({"UPC": upc})
    if r_doc and m_doc:
        print(f"UPC {upc}: Raw Brand '{r_doc.get('BRAND')}' -> Master Brand '{m_doc.get('BRAND')}'")

# Search for SNAZK items
snazk_items = list(raw.find({"BRAND": "SNAZK"}).limit(2))
for si in snazk_items:
    item_name = si.get("ITEM", "")
    # Search in ITEM or MERGE_ITEMS
    m_doc = master.find_one({"$or": [{"ITEM": item_name}, {"MERGE_ITEMS": {"$regex": re.escape(item_name) if item_name else "XXXX"}}]})
    if m_doc:
         print(f"Item '{item_name[:20]}': Raw Brand 'SNAZK' -> Master Brand '{m_doc.get('BRAND')}'")
    else:
         print(f"Item '{item_name[:20]}': SNAZK not found in Master")
