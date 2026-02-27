import os
import pandas as pd
from pymongo import MongoClient
import re

def connect_db():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    return db['mapping_results'], db['7-eleven_data'], db['master_stock_data']

def categorize_failures():
    coll_res, coll_7e, coll_master = connect_db()
    path_bench = r'd:\git\FMCG_Dashboard\ARNOTTS_7-ELEVEN_RAW.xlsx'
    
    df_bench = pd.read_excel(path_bench)
    bench_codes = [int(x) for x in df_bench['ArticleCode'].unique()]
    
    mapped_codes = set([int(d['ArticleCode']) for d in coll_res.find({"Match_Level": {"$ne": "GAP"}, "ArticleCode": {"$ne": None}}, {"ArticleCode": 1})])
    
    missing_codes = [c for c in bench_codes if c not in mapped_codes]
    
    patterns = {
        "BRAND_NOT_FOUND": [],
        "VARIANT_MISMATCH": [],
        "SIZE_MISMATCH": [],
        "NO_DATA_IN_7E": []
    }
    
    for code in missing_codes:
        doc_7e = coll_7e.find_one({"ArticleCode": code})
        if not doc_7e:
            patterns["NO_DATA_IN_7E"].append(code)
            continue
            
        brand = doc_7e.get("7E_Brand", "NA").upper()
        variant = doc_7e.get("7E_Variant", "NA").upper()
        flavour = doc_7e.get("7E_flavour", "NA").upper()
        size = float(re.search(r'(\d+)', str(doc_7e.get("7E_Nrmsize", "0"))).group(1)) if re.search(r'(\d+)', str(doc_7e.get("7E_Nrmsize", "0"))) else 0.0
        
        # Check if brand exists in Master Stock
        brand_exists = coll_master.find_one({"BRAND": {"$regex": re.escape(brand), "$options": "i"}})
        if not brand_exists:
            # Check for close matches
            # (Simplified check for this script)
            patterns["BRAND_NOT_FOUND"].append({"code": code, "brand": brand, "desc": doc_7e.get("ArticleDescription")})
            continue
            
        # If brand exists, check if variant/size is the issue
        # Look for the brand items in master
        master_items = list(coll_master.find({"BRAND": {"$regex": re.escape(brand), "$options": "i"}}))
        
        var_found = False
        size_found = False
        
        for m in master_items:
            m_var = str(m.get("VARIANT", "NA")).upper()
            m_flav = str(m.get("flavour", "NA")).upper()
            m_size = float(re.search(r'(\d+)', str(m.get("NRMSIZE", "0"))).group(1)) if re.search(r'(\d+)', str(m.get("NRMSIZE", "0"))) else 0.0
            
            if variant in m_var or m_var in variant or flavour in m_var or m_var in flavour or flavour in m_flav:
                var_found = True
                if abs(size - m_size) <= 5.0:
                    size_found = True
                    break
        
        if not var_found:
            patterns["VARIANT_MISMATCH"].append({"code": code, "brand": brand, "7e_var": variant, "7e_flav": flavour, "desc": doc_7e.get("ArticleDescription")})
        elif not size_found:
            patterns["SIZE_MISMATCH"].append({"code": code, "brand": brand, "7e_size": size, "desc": doc_7e.get("ArticleDescription")})

    print("\n--- FAILURE CATEGORIZATION ---")
    for pat, items in patterns.items():
        print(f"{pat}: {len(items)}")
        for it in items[:3]:
            print(f"  - {it}")

if __name__ == "__main__":
    categorize_failures()
