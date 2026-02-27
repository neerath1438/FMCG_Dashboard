from pymongo import MongoClient
import re

def normalize_text(text):
    if not text:
        return 'NA'
    text = str(text).upper().strip()
    if text in ['NONE', 'NORMAL', '', 'NA']:
        return 'NA'
    return text

def parse_size(size_str):
    if not size_str:
        return 0.0
    size_str = str(size_str).upper().replace('GM', 'G')
    match = re.search(r'(\d+(\.\d+)?)', size_str)
    if match:
        return float(match.group(1))
    return 0.0

def debug_lookup():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    col = db['7-eleven_data']
    
    print("Sample 7-Eleven Lookup Generation:")
    for doc in col.find().limit(10):
        brand = normalize_text(doc.get('Brand'))
        variant = normalize_text(doc.get('7E_Variant'))
        mpack = normalize_text(doc.get('7E_MPack'))
        size = parse_size(doc.get('7E_Nrmsize'))
        flavour = normalize_text(doc.get('7E_flavour'))
        
        print(f"Key: {(brand, variant, mpack)} | Flavour: {flavour} | Size: {size} | Desc: {doc.get('ArticleDescription')[:30]}")

if __name__ == "__main__":
    debug_lookup()
