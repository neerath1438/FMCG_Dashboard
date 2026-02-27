import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = client['fmcg_mastering']
    return db['mapping_results'], db['master_stock_data']

def parse_size(s):
    if not s: return 0.0
    match = re.search(r"(\d+(\.\d+)?)", str(s))
    return float(match.group(1)) if match else 0.0

def research_gaps():
    coll_res, coll_master = connect_db()
    
    # 1. Get a variety of GAPs (different categories/brands)
    gaps = list(coll_res.find({"Match_Level": "GAP"}).limit(100))
    master_docs = list(coll_master.find())
    
    print("\n" + "="*80)
    print("AI GAP RESEARCH REPORT")
    print("="*80)
    
    found_possibilities = 0
    for g in gaps:
        desc = g.get("ArticleDescription")
        brand = g.get("7E_Brand", "UNKNOWN")
        variant = g.get("7E_Variant", "NONE")
        flavour = g.get("7E_flavour", "NONE")
        size = g.get("7E_Size")
        
        # Search for candidates in master stock by fuzzy brand or any overlapping words
        brand_keywords = [b.strip() for b in str(brand).split() if len(b) > 2]
        
        candidates = []
        for m in master_docs:
            m_item = str(m.get("ITEM", "")).upper()
            m_brand = str(m.get("BRAND", "")).upper()
            
            # Check for brand match or keyword overlap
            if brand.upper() in m_brand or m_brand in brand.upper():
                candidates.append(m)
            elif any(k.upper() in m_item for k in brand_keywords):
                candidates.append(m)
                
        if candidates:
            found_possibilities += 1
            print(f"\n7-Eleven (GAP): {desc}")
            print(f"  Extracted -> Brand: {brand}, Var: {variant}, Flav: {flavour}, Size: {size}")
            print(f"  [Potential Matches in Master Stock]:")
            
            # Limit candidates to show only the most relevant sounding ones
            for c in candidates[:5]:
                print(f"    - Nielsen Item: {c.get('ITEM')}")
                print(f"      (Brand: {c.get('BRAND')}, Var: {c.get('VARIANT')}, Size: {c.get('NRMSIZE')})")
            print("-" * 40)

        if found_possibilities >= 30: # Look at 30 decent ones
            break

if __name__ == "__main__":
    research_gaps()
