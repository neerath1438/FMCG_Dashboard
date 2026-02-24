import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

def find_details_for_client():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    q = {'Markets': 'Pen Malaysia', 'Facts': 'Sales Value'}
    
    # Raw data
    raw_docs = list(db['raw_data'].find(q))
    df_raw = pd.DataFrame(raw_docs)
    
    # 3 Dropped Records (ITEM is null)
    dropped = df_raw[df_raw['ITEM'].isnull()]
    print("--- 3 DROPPED RECORDS (NULL ITEM) ---")
    for _, row in dropped.iterrows():
        print(f"ID: {row['_id']} | ITEM: {row.get('ITEM')} | UPC: {row.get('UPC')}")
    
    # 4 Merged Records (Duplicates)
    # Strategy: Find groups in raw data that have multiple records but represent the same product
    # The logic used in processor.py: UPC, Markets, MPACK, Facts, Size(5g)
    
    # Let's see which UPCs appear multiple times in raw data
    upc_counts = df_raw['UPC'].value_counts()
    dup_upcs = upc_counts[upc_counts > 1].index.tolist()
    
    print("\n--- 4 MERGED RECORDS (DUPLICATES) ---")
    for upc in dup_upcs:
        group = df_raw[df_raw['UPC'] == upc]
        # We need to see if they were merged or just distinct
        # If they have same ITEM and SIZE, they are definitely duplicates
        if len(group) > 1:
            print(f"\nUPC: {upc} found {len(group)} times in Raw Data:")
            for _, row in group.iterrows():
                print(f"  -> ID: {row['_id']} | ITEM: {row.get('ITEM')} | SIZE: {row.get('NRMSIZE')}")

if __name__ == "__main__":
    find_details_for_client()
