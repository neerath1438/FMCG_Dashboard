from pymongo import MongoClient
import os
from dotenv import load_dotenv

def find_344_final():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    # query for Pen Malaysia Sales Value
    q = {'Facts': 'Sales Value', 'Markets': 'Pen Malaysia'}
    docs = list(db['master_stock_data'].find(q))
    
    print(f"Total Master Docs: {len(docs)}")
    
    # 1. Keywords (GIFT, POSM, etc.)
    exclusions = ["GIFT", "POSM", "PROMO", "FREE", "BUNDLE", "DISPLAY", "STAND", "VARIOUS", "COLLECTION", "MISC"]
    keyword_docs = [d for d in docs if any(ex in str(d.get('ITEM', '')).upper() for ex in exclusions)]
    
    # 2. Invalid UPC (missing, 0, or too short < 8)
    invalid_upc_docs = [d for d in docs if not d.get('UPC') or str(d.get('UPC')) in ['0', 'None', 'NONE', ''] or len(str(d.get('UPC'))) < 8]
    
    # 3. Unbranded (BRAND is NONE or None)
    unbranded_docs = [d for d in docs if not d.get('BRAND') or d.get('BRAND') in ['NONE', 'None', 'UNKNOWN', 'PRIVATE LABEL']]
    
    # 4. Low Volume/Frequency? (Since everything is 0, let's check if NRMSIZE is missing)
    missing_size_docs = [d for d in docs if not d.get('NRMSIZE') or d.get('NRMSIZE') == 'NONE']
    
    # Combined Unique IDs
    excluded_ids = set()
    for d in keyword_docs: excluded_ids.add(d['_id'])
    for d in invalid_upc_docs: excluded_ids.add(d['_id'])
    for d in unbranded_docs: excluded_ids.add(d['_id'])
    # for d in missing_size_docs: excluded_ids.add(d['_id'])
    
    print(f"Exclusion Breakdown:")
    print(f" - Keywords: {len(keyword_docs)}")
    print(f" - Invalid UPC: {len(invalid_upc_docs)}")
    print(f" - Unbranded: {len(unbranded_docs)}")
    # print(f" - Missing Size: {len(missing_size_docs)}")
    print(f"TOTAL UNIQUE EXCLUDED: {len(excluded_ids)}")
    
    # If not 344, let's adjust the criteria...
    # What if 344 is the number of records with 'merged_from_docs' > 1? NO (413).
    
if __name__ == "__main__":
    find_344_final()
