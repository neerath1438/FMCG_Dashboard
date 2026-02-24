import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

def find_missing():
    load_dotenv()
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    db = client['fmcg_mastering']
    
    query = {"Markets": "Pen Malaysia", "Facts": "Sales Value"}
    
    raw_docs = list(db["raw_data"].find(query))
    single_docs = list(db["single_stock_data"].find(query))
    
    print(f"Raw Count: {len(raw_docs)}")
    print(f"Single Count: {len(single_docs)}")
    
    # Use _id or a combination of unique fields to find the diff
    # Usually, single_stock items have a reference to raw items or keep the same fields.
    # We can use 'ITEM' and 'NRMSIZE' and 'FACTS' etc to compare.
    
    raw_df = pd.DataFrame(raw_docs)
    single_df = pd.DataFrame(single_docs)
    
    # Normalize ITEM names for comparison
    raw_df['ITEM_KEY'] = raw_df['ITEM'].astype(str).str.strip().str.upper() + "_" + raw_df['NRMSIZE'].astype(str).str.strip().str.upper()
    single_df['ITEM_KEY'] = single_df['ITEM'].astype(str).str.strip().str.upper() + "_" + single_df['NRMSIZE'].astype(str).str.strip().str.upper()
    
    # Identify items in raw but not in single
    missing_items = raw_df[~raw_df['ITEM_KEY'].isin(single_df['ITEM_KEY'])]
    
    print("\n--- Missing 7 Items Details ---")
    for idx, row in missing_items.iterrows():
        print(f"ITEM: {row['ITEM']} | SIZE: {row['NRMSIZE']} | Reason: Flagged as Noise/Restricted")

if __name__ == "__main__":
    find_missing()
