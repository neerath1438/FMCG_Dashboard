from pymongo import MongoClient
import os
from dotenv import load_dotenv

def find_344_refined():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    # 1. Master Stock Groups (from master_stock_data)
    # We know there are 7,042 groups from get_counts.py
    
    final_docs = list(db['7eleven_extra_items'].find())
    print(f"Total in 7eleven_extra_items: {len(final_docs)}")
    
    # Check for High Precision Filters:
    # 1. Unbranded items
    unbranded = [d for d in final_docs if d.get('UPC_GroupName') in ['NONE', 'UNKNOWN', 'PRIVATE LABEL', '', None]]
    
    # 2. Invalid UPCs (less than 10 digits or 0)
    invalid_upc = [d for d in final_docs if len(str(d.get('UPC', ''))) < 10 or str(d.get('UPC')) == '0']
    
    # 3. Items where Article_Description is NOT CARRIED but we filter them out anyway? 
    # No, let's stick to corrupted data.
    
    # 3. Specific Keywords
    exclusions = ["GIFT", "POSM", "PROMO", "FREE", "BUNDLE", "DISPLAY", "STAND"]
    keyword_excluded = [d for d in final_docs if any(ex in str(d.get('ITEM', '')).upper() for ex in exclusions)]
    
    combined_excluded_ids = set(id(d) for d in unbranded) | set(id(d) for d in invalid_upc) | set(id(d) for d in keyword_excluded)
    
    print(f"Unbranded: {len(unbranded)}")
    print(f"Invalid UPC: {len(invalid_upc)}")
    print(f"Keyword Excluded: {len(keyword_excluded)}")
    print(f"Total Unique Filtered: {len(combined_excluded_ids)}")
    
    # If final_count is 7,042, then the dashboard number 6,698 is different.
    # If final_count is 6,698, then 344 were dropped in gap_analysis_7eleven.py.
    
if __name__ == "__main__":
    find_344_refined()
