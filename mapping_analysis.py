import os
import re
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

def connect_db():
    """Connects to MongoDB and returns the database and collections."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client['fmcg_mastering']
    return db, db['7-eleven_data'], db['master_stock_data'], db['mapping_results']

def normalize_text(text):
    """Standardizes text: uppercase, removes extra spaces, handles None."""
    if not text:
        return "NA"
    text = str(text).upper().strip()
    if text in ["NONE", "NORMAL", "", "NA"]:
        return "NA"
    return text

def parse_size(size_str):
    """Extracts numeric value from size string (e.g., '300G' -> 300.0)."""
    if not size_str:
        return 0.0
    size_str = str(size_str).upper().replace("GM", "G")
    match = re.search(r"(\d+(\.\d+)?)", size_str)
    if match:
        return float(match.group(1))
    return 0.0

def get_7eleven_lookup(coll_7e):
    """Creates a lookup dictionary for attribute-based matching."""
    print("Building 7-Eleven lookup dictionary for mapping...")
    lookup = {}
    for doc in coll_7e.find():
        brand = normalize_text(doc.get("L4_Description_Brand"))
        variant = normalize_text(doc.get("7E_Variant"))
        mpack = normalize_text(doc.get("7E_MPack"))
        size_val = parse_size(doc.get("7E_Nrmsize"))
        
        key = (brand, variant, mpack)
        if key not in lookup:
            lookup[key] = []
        
        lookup[key].append({
            "id": doc["_id"],
            "article_code": doc.get("ArticleCode"),
            "gtin": doc.get("GTIN"),
            "desc": doc.get("ArticleDescription"),
            "size_val": size_val
        })
    return lookup

def run_mapping():
    db, coll_7e, coll_master, coll_results = connect_db()
    
    # Clear previous results
    coll_results.delete_many({})
    print("Previous results cleared.")
    
    # 1. Build lookup for Level 2
    lookup_7e = get_7eleven_lookup(coll_7e)
    
    # 2. Build direct UPC lookup for Level 1
    upc_lookup_7e = {doc.get("GTIN"): doc for doc in coll_7e.find() if doc.get("GTIN")}
    
    master_docs = list(coll_master.find())
    print(f"Starting mapping for {len(master_docs)} Master Stock items...")
    
    results = []
    
    for master in master_docs:
        upc = master.get("UPC")
        brand = normalize_text(master.get("BRAND"))
        variant = normalize_text(master.get("VARIANT") or master.get("flavour") or master.get("variant"))
        mpack = normalize_text(master.get("MPACK"))
        size_val = parse_size(master.get("NRMSIZE") or master.get("size"))
        
        match_level = "GAP"
        match_type = "No Match Found"
        matched_7e = None
        
        # --- Level 1: Exact UPC Match ---
        if upc and upc in upc_lookup_7e:
            matched_7e = upc_lookup_7e[upc]
            match_level = "LEVEL_1"
            match_type = "Exact UPC Match (UPC == GTIN)"
        
        # --- Level 2: Attribute Match (if Level 1 failed) ---
        else:
            candidates = lookup_7e.get((brand, variant, mpack), [])
            for cand in candidates:
                # Tolerance check: ±5g
                if abs(cand['size_val'] - size_val) <= 5.0:
                    matched_7e = cand
                    match_level = "LEVEL_2"
                    match_type = "Attribute Match (Brand+Variant+MPack+Size±5g)"
                    break # Stop at first good match
        
        # --- Prepare Result Record ---
        result_record = {
            # Client Required Fields
            "UPC": upc,
            "ITEM": master.get("ITEM"),
            "Main_UPC": (matched_7e.get("GTIN") if match_level == "LEVEL_1" else 
                         (matched_7e.get("gtin") if match_level == "LEVEL_2" else upc)),
            "UPC_GroupName": f"{brand} | {variant} | {size_val}G",
            "ArticleCode": matched_7e.get("ArticleCode") if match_level == "LEVEL_1" else matched_7e.get("article_code") if match_level == "LEVEL_2" else None,
            "GTIN": matched_7e.get("GTIN") if match_level == "LEVEL_1" else matched_7e.get("gtin") if match_level == "LEVEL_2" else None,
            "Article_Description": matched_7e.get("ArticleDescription") if match_level == "LEVEL_1" else matched_7e.get("desc") if match_level == "LEVEL_2" else None,
            
            # QA / Technical Fields
            "qa_fields": {
                "match_level": match_level,
                "match_type": match_type,
                "matched_7e_id": str(matched_7e.get("_id") if match_level == "LEVEL_1" else matched_7e.get("id") if match_level == "LEVEL_2" else None),
                "original_brand": master.get("BRAND"),
                "original_size": master.get("NRMSIZE"),
                "process_date": datetime.now().isoformat()
            }
        }
        results.append(result_record)
    
    if results:
        coll_results.insert_many(results)
        print(f"Mapping complete. {len(results)} records inserted into 'mapping_results'.")
        generate_qa_report(coll_results)

def generate_qa_report(coll_results):
    print("\n--- QA Mapping Report ---")
    total = coll_results.count_documents({})
    l1 = coll_results.count_documents({"qa_fields.match_level": "LEVEL_1"})
    l2 = coll_results.count_documents({"qa_fields.match_level": "LEVEL_2"})
    gaps = coll_results.count_documents({"qa_fields.match_level": "GAP"})
    
    print(f"Total Master Stock Items: {total}")
    print(f"Level 1 Matches (UPC):    {l1} ({round(l1/total*100, 2) if total else 0}%)")
    print(f"Level 2 Matches (ATTR):   {l2} ({round(l2/total*100, 2) if total else 0}%)")
    print(f"Missing in 7-Eleven:      {gaps} ({round(gaps/total*100, 2) if total else 0}%)")
    print("-" * 25)

def export_results():
    db, _, _, coll_results = connect_db()
    data = list(coll_results.find({}, {"_id": 0}))
    
    # Flatten just the top level for client CSV
    client_data = []
    for d in data:
        row = {k: v for k, v in d.items() if k != "qa_fields"}
        client_data.append(row)
        
    df = pd.DataFrame(client_data)
    df.to_excel("Mapping_Analysis_Export.xlsx", index=False)
    print("Results exported to Mapping_Analysis_Export.xlsx")

if __name__ == "__main__":
    run_mapping()
    export_results()
