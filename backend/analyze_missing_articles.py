import os
import pandas as pd
from pymongo import MongoClient
import re

def connect_db():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    return db['mapping_results'], db['7-eleven_data'], db['master_stock_data']

def analyze_missing():
    coll_res, coll_7e, coll_master = connect_db()
    
    # 1. Load Benchmark ArticleCodes
    path_bench = r'POCKY_7-ELEVEN_RAW.xlsx' # Using Pocky or Arnotts based on previous context
    # User mentioned 649, which matches ARNOTTS_7-ELEVEN_RAW.xlsx from previous logs
    path_bench = r'd:\git\FMCG_Dashboard\ARNOTTS_7-ELEVEN_RAW.xlsx'
    
    if not os.path.exists(path_bench):
        print(f"Error: Benchmark file not found at {path_bench}")
        return

    df_bench = pd.read_excel(path_bench)
    bench_codes = set(df_bench['ArticleCode'].unique())
    print(f"Total Unique ArticleCodes in Benchmark: {len(bench_codes)}")

    # 2. Get Mapped ArticleCodes (Non-GAP)
    mapped_docs = list(coll_res.find({"Match_Level": {"$ne": "GAP"}}, {"ArticleCode": 1}))
    mapped_codes = set([d.get("ArticleCode") for d in mapped_docs if d.get("ArticleCode")])
    print(f"Total Unique ArticleCodes Mapped: {len(mapped_codes)}")

    # 3. Identify Missing
    missing_codes = list(bench_codes - mapped_codes)
    print(f"Missing ArticleCodes: {len(missing_codes)}")

    # 4. Detailed Analysis of Missing Items
    print("\n" + "="*80)
    print("DETAILED ANALYSIS OF MISSING ARTICLES")
    print("="*80)
    
    for code in missing_codes[:20]: # Show first 20 for analysis
        # Convert numpy.int64 to plain int for MongoDB
        search_code = int(code)
        # Get details from 7e_data
        doc_7e = coll_7e.find_one({"ArticleCode": search_code})
        if not doc_7e:
            # Try to find in bench df
            row = df_bench[df_bench['ArticleCode'] == code].iloc[0]
            print(f"\n[GAP] ArticleCode: {code}")
            print(f"  Desc: {row.get('ArticleDescription')}")
            print(f"  (Not found in MongoDB 7-eleven_data)")
            continue
            
        desc = doc_7e.get("ArticleDescription")
        brand = doc_7e.get("7E_Brand")
        variant = doc_7e.get("7E_Variant")
        flavour = doc_7e.get("7E_flavour")
        size = doc_7e.get("7E_Nrmsize")
        
        print(f"\n[GAP] ArticleCode: {code}")
        print(f"  Desc: {desc}")
        print(f"  Extracted -> Brand: {brand}, Var: {variant}, Flav: {flavour}, Size: {size}")
        
        # Searching for potential matches in master stock by brand
        search_brand = str(brand).upper()
        potentials = list(coll_master.find({"BRAND": {"$regex": re.escape(search_brand), "$options": "i"}}, {"ITEM": 1, "VARIANT": 1, "NRMSIZE": 1}).limit(5))
        
        if potentials:
            print(f"  [Potential Candidates in Master Stock]:")
            for p in potentials:
                print(f"    - {p.get('ITEM')} (Var: {p.get('VARIANT')}, Size: {p.get('NRMSIZE')})")
        else:
            print(f"  [No Brand Match in Master Stock for '{brand}']")
            # Try keyword match from description
            keywords = [k for k in desc.split() if len(k) > 2][:3]
            kw_regex = "|".join([re.escape(k) for k in keywords])
            kw_potentials = list(coll_master.find({"ITEM": {"$regex": kw_regex, "$options": "i"}}, {"ITEM": 1, "BRAND": 1}).limit(3))
            if kw_potentials:
                print(f"  [Keyword Candidates]:")
                for kp in kw_potentials:
                    print(f"    - {kp.get('ITEM')} (Brand: {kp.get('BRAND')})")

if __name__ == "__main__":
    analyze_missing()
