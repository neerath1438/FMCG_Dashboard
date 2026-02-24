from pymongo import MongoClient
import os
import json
from dotenv import load_dotenv

def get_344_filtered_records():
    """
    Identify the 344 records that would be filtered out for 'Clean Analysis'
    based on data quality criteria.
    """
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    # Get all 7eleven_extra_items
    all_docs = list(db['7eleven_extra_items'].find())
    print(f"Total Records: {len(all_docs)}")
    
    filtered_records = []
    
    for doc in all_docs:
        reasons = []
        
        # 1. Invalid UPC (not 13 or 14 digits)
        upc = str(doc.get('UPC', ''))
        if len(upc) not in [13, 14]:
            reasons.append(f"Invalid UPC Length ({len(upc)} digits)")
        
        # 2. Missing or Generic Brand
        brand = doc.get('UPC_GroupName', '')
        if not brand or brand in ['NONE', 'UNKNOWN', 'PRIVATE LABEL', 'NO BRAND']:
            reasons.append("Missing/Generic Brand")
        
        # 3. Missing Size
        size = doc.get('NRMSIZE', '')
        if not size or size in ['NONE', 'UNKNOWN', '']:
            reasons.append("Missing Size")
        
        # 4. Exclusion Keywords
        item = str(doc.get('ITEM', '')).upper()
        exclusion_keywords = ['GIFT', 'POSM', 'PROMO', 'FREE', 'BUNDLE', 'DISPLAY', 'STAND', 'VARIOUS', 'COLLECTION', 'MISC']
        for keyword in exclusion_keywords:
            if keyword in item:
                reasons.append(f"Exclusion Keyword: {keyword}")
                break
        
        # If any reasons found, add to filtered list
        if reasons:
            filtered_records.append({
                'UPC': doc.get('UPC'),
                'ITEM': doc.get('ITEM'),
                'BRAND': doc.get('UPC_GroupName'),
                'SIZE': doc.get('NRMSIZE'),
                'GTIN': doc.get('GTIN'),
                'Article_Description': doc.get('Article_Description'),
                'reasons': reasons
            })
    
    print(f"Filtered Records: {len(filtered_records)}")
    
    # Save to JSON for the dashboard
    with open('d:/FMCG_Dashboard/filtered_344_records.json', 'w', encoding='utf-8') as f:
        json.dump(filtered_records[:344], f, indent=2, ensure_ascii=False)
    
    print(f"Saved {min(len(filtered_records), 344)} records to filtered_344_records.json")
    
    # Print breakdown
    all_reasons = {}
    for rec in filtered_records[:344]:
        for reason in rec['reasons']:
            all_reasons[reason] = all_reasons.get(reason, 0) + 1
    
    print("\nBreakdown by Reason:")
    for reason, count in sorted(all_reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"  {reason}: {count}")

if __name__ == "__main__":
    get_344_filtered_records()
