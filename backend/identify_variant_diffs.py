import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = client['fmcg_mastering']
    return db['mapping_results'], db['master_stock_data']

def normalize(text):
    if not text: return "NA"
    return str(text).upper().strip()

def parse_size(s):
    if not s: return 0.0
    match = re.search(r"(\d+(\.\d+)?)", str(s))
    return float(match.group(1)) if match else 0.0

def analyze():
    coll_res, coll_master = connect_db()
    gaps = list(coll_res.find({"Match_Level": "GAP"}))
    master_docs = list(coll_master.find())

    print("\n--- Why they don't match (Variant/Flavour Differences) ---\n")
    
    found = 0
    for g in gaps:
        b_7e = normalize(g.get("7E_Brand"))
        s_7e = parse_size(g.get("7E_Size"))
        v_7e = normalize(g.get("7E_Variant"))
        f_7e = normalize(g.get("7E_Flavour"))
        desc_7e = g.get("ArticleDescription")

        # Find master items with same brand and size
        potentials = []
        for m in master_docs:
            if normalize(m.get("BRAND")) == b_7e:
                m_size = parse_size(m.get("NRMSIZE") or m.get("size"))
                if abs(m_size - s_7e) <= 1.0:
                    potentials.append(m)
        
        if potentials:
            found += 1
            print(f"7-Eleven Item: {desc_7e}")
            print(f"  -> Extracted: Var={v_7e}, Flav={f_7e}, Size={s_7e}g")
            for p in potentials:
                v_n = normalize(p.get("VARIANT") or p.get("variant"))
                f_n = normalize(p.get("flavour"))
                print(f"  -> Nielsen Match Candidate: {p.get('ITEM')}")
                print(f"     (Nielsen Var={v_n}, Flav={f_n}, Size={parse_size(p.get('NRMSIZE') or p.get('size'))}g)")
            print("-" * 50)
        
        if found >= 10: break

if __name__ == "__main__":
    analyze()
