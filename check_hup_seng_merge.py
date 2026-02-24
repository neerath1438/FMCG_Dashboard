from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017")
db = client["fmcg_mastering"]
master_coll = db["master_stock_data"]
raw_coll = db["raw_data"]

def check_items():
    items_to_check = [
        "HUP SENG CREAM CRACKER 12X428 GM",
        "HUP SENG CRM CRACKER 428GMX12"
    ]
    
    results = {
        "raw_data": [],
        "master_stock_data": []
    }
    
    for item in items_to_check:
        doc = raw_coll.find_one({"ITEM": item})
        if doc:
            results["raw_data"].append({"item": item, "found": True, "upc": doc.get('UPC')})
        else:
            regex_doc = raw_coll.find_one({"ITEM": {"$regex": item.replace(" ", ".*"), "$options": "i"}})
            if regex_doc:
                results["raw_data"].append({"item": item, "found": "Regex", "matched_item": regex_doc.get('ITEM'), "upc": regex_doc.get('UPC')})
            else:
                results["raw_data"].append({"item": item, "found": False})

    for item in items_to_check:
        master_doc = master_coll.find_one({"merge_items": item})
        if master_doc:
            results["master_stock_data"].append({
                "queried_item": item,
                "master_item": master_doc.get('ITEM'),
                "merge_id": master_doc.get('merge_id'),
                "merge_items": master_doc.get('merge_items'),
                "attributes": {
                    "brand": master_doc.get('brand'),
                    "flavour": master_doc.get('flavour'),
                    "size": master_doc.get('size')
                }
            })
        else:
            results["master_stock_data"].append({"queried_item": item, "found": False})

    with open("hup_seng_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    check_items()

if __name__ == "__main__":
    check_items()
