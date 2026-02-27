import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_db():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client['fmcg_mastering']
    return db, db['mapping_results'], db['master_stock_data']

def normalize(text):
    if not text: return "NA"
    return str(text).upper().strip()

def parse_size(s):
    if not s: return 0.0
    match = re.search(r"(\d+(\.\d+)?)", str(s))
    return float(match.group(1)) if match else 0.0

def analyze_gaps():
    db, coll_res, coll_master = connect_db()
    
    gaps = list(coll_res.find({"Match_Level": "GAP"}))
    master_docs = list(coll_master.find())
    
    print(f"Analyzing {len(gaps)} Gap Articles...\n")
    
    categories = {
        "Brand Not in Master": 0,
        "Size Mismatch (>5g)": 0,
        "Variant/Flavour Mismatch": 0,
        "No Similarity Found": 0
    }
    
    samples = []
    
    for g in gaps:
        b_7e = normalize(g.get("7E_Brand"))
        v_7e = normalize(g.get("7E_Variant"))
        f_7e = normalize(g.get("7E_Flavour"))
        s_7e = parse_size(g.get("7E_Size"))
        desc_7e = normalize(g.get("ArticleDescription"))
        
        # 1. Check if Brand exists in Master at all
        master_with_brand = [m for m in master_docs if normalize(m.get("BRAND")) == b_7e]
        
        if not master_with_brand:
            categories["Brand Not in Master"] += 1
            if len(samples) < 5:
                samples.append(f"BRAND GAP: {b_7e} | {desc_7e} (Brand '{b_7e}' not found in Nielsen)")
            continue
            
        # 2. Brand exists, check for size mismatch
        # Look for items with branding match but different size
        close_items = []
        size_mismatch = False
        for m in master_with_brand:
            m_size = parse_size(m.get("NRMSIZE") or m.get("size"))
            size_diff = abs(m_size - s_7e)
            
            if size_diff > 5.0 and size_diff <= 50.0:
                size_mismatch = True
                close_items.append(f"{m.get('ITEM')} ({m_size}g)")
        
        if size_mismatch and not any(parse_size(m.get("NRMSIZE") or m.get("size")) == s_7e for m in master_with_brand):
            categories["Size Mismatch (>5g)"] += 1
            if len(samples) < 15:
                samples.append(f"SIZE GAP: {desc_7e} ({s_7e}g) -> Potentials in Nielsen: {', '.join(close_items[:2])}")
            continue

        # 3. Brand and Size might exist, but Variant/Flavour doesn't match
        categories["Variant/Flavour Mismatch"] += 1
        if len(samples) < 25:
             # Try to find what variants DO exist for this brand/size
             existing_variants = list(set([normalize(m.get("VARIANT") or m.get("flavour") or m.get("variant")) for m in master_with_brand if parse_size(m.get("NRMSIZE") or m.get("size")) == s_7e]))
             samples.append(f"VARIANT GAP: {desc_7e} (7E Variant: {v_7e}, Flavour: {f_7e}) -> Nielsen has: {existing_variants}")

    print("--- GAP CATEGORIZATION ---")
    for cat, count in categories.items():
        print(f"{cat}: {count} ({round(count/len(gaps)*100, 1)}%)")
        
    print("\n--- SAMPLE FAILURES ---")
    for s in samples[:15]:
        print(f"• {s}")

if __name__ == "__main__":
    analyze_gaps()
