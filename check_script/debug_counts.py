from pymongo import MongoClient
import os
from dotenv import load_dotenv

def find_missing_records():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    # 1. Targeted Nielsen (Source)
    query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
    source_upcs = set()
    source_docs = list(db["master_stock_data"].find(query))
    for doc in source_docs:
        # Use a composite key because UPCs can be duplicate
        key = f"{doc.get('UPC')}|{doc.get('ITEM')}|{doc.get('NRMSIZE')}"
        source_upcs.add(key)
    
    # 2. Final Report (Result)
    report_upcs = set()
    report_docs = list(db["7eleven_extra_items"].find())
    for doc in report_docs:
        key = f"{doc.get('UPC')}|{doc.get('ITEM')}|{doc.get('NRMSIZE')}" # Wait, NRMSIZE might not be in report
        # Let's check keys in report
        if 'ITEM' in doc:
            key = f"{doc.get('UPC')}|{doc.get('ITEM')}"
            report_upcs.add(key)
    
    # Let's do a simpler comparison by just UPC first
    source_only_upcs = set(str(d.get('UPC')) for d in source_docs)
    report_only_upcs = set(str(d.get('UPC')) for d in report_docs)
    
    missing_upcs = source_only_upcs - report_only_upcs
    
    print(f"Source Records: {len(source_docs)}")
    print(f"Report Records: {len(report_docs)}")
    print(f"Unique UPCs in Source: {len(source_only_upcs)}")
    print(f"Unique UPCs in Report: {len(report_only_upcs)}")
    print(f"UPCs in Source but not in Report: {len(missing_upcs)}")
    
    if missing_upcs:
        print("Sample Missing UPCs:")
        for upc in list(missing_upcs)[:10]:
            print(f" - {upc}")

if __name__ == "__main__":
    find_missing_records()
