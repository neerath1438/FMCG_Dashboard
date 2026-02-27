import pandas as pd
from pymongo import MongoClient
import os

def check_cache_coverage():
    excel_path = r'd:\git\FMCG_Dashboard\backend\Wersel_7E_Data.xlsx'
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    cache_col = db['7-eleven_llm_cache']
    
    # 1. Get unique descriptions from Excel
    df = pd.read_excel(excel_path)
    excel_descs = set(df['ArticleDescription'].unique())
    excel_count = len(excel_descs)
    
    # 2. Get all descriptions in Cache
    cache_descs = set(cache_col.distinct("article_description"))
    cache_count = len(cache_descs)
    
    # 3. Intersection and Differences
    missing_in_cache = excel_descs - cache_descs
    extra_in_cache = cache_descs - excel_descs
    
    print(f"Excel Unique Descriptions: {excel_count}")
    print(f"Cache Unique Descriptions: {cache_count}")
    print(f"Matched (Found in both):   {len(excel_descs & cache_descs)}")
    print(f"Missing in Cache:         {len(missing_in_cache)}")
    print(f"Extra in Cache (Other):    {len(extra_in_cache)}")
    
    if missing_in_cache:
        print("\nFirst 5 missing descriptions:")
        for d in list(missing_in_cache)[:5]:
            print(f" - {d}")

if __name__ == "__main__":
    check_cache_coverage()
