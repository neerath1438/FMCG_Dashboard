from pymongo import MongoClient
import os
import pandas as pd
from dotenv import load_dotenv

def find_missing_344():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    # 1. Get Master Stock Groups (7,042)
    # We'll simulate the grouping to find the IDs
    query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
    nielsen_docs = list(db["master_stock_data"].find(query))
    df_nielsen = pd.DataFrame(nielsen_docs)
    
    # 2. Get Final Analysis IDs
    # These are the ones that actually made it to the report
    report_items = list(db["7eleven_extra_items"].find())
    report_upcs = set(str(d.get('UPC')) for d in report_items)
    
    # 3. Find items in master_stock_data that are NOT in the report
    missing = []
    for doc in nielsen_docs:
        if str(doc.get('UPC')) not in report_upcs:
            missing.append(doc)
            
    print(f"Total Missing Items: {len(missing)}")
    
    if missing:
        df_missing = pd.DataFrame(missing)
        # Check reasons: nulls, or if they are from specific markets/facts that were filtered out later
        print("\n--- Reasons / Patterns in Missing Items ---")
        print(f"Items with Null BRAND: {df_missing['BRAND'].isna().sum() + (df_missing['BRAND'] == 'NONE').sum()}")
        print(f"Items with Null Variant/Size: {df_missing['VARIANT'].isna().sum() + (df_missing['NRMSIZE'].isna().sum())}")
        
        print("\nSample Missing Items:")
        for doc in missing[:10]:
            print(f"- {doc.get('ITEM')} | BRAND: {doc.get('BRAND')} | UPC: {doc.get('UPC')}")

if __name__ == "__main__":
    find_missing_344()
