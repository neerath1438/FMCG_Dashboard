import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

def export_sales_value_to_excel():
    # Load environment variables
    load_dotenv()
    
    # MongoDB Connection Details
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    collection_name = "master_stock_data"
    output_file = "sales_value_data.xlsx"
    
    print(f"Connecting to MongoDB at {mongo_uri}...")
    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        # Query for 'Sales Value' facts
        print("Querying documents with Facts = 'Sales Value'...")
        # No delete operations here, only find()
        cursor = collection.find({"Facts": "Sales Value"})
        
        # Fetch all results
        data = list(cursor)
        
        if not data:
            print("No documents found with Facts = 'Sales Value'.")
            return
        
        print(f"Found {len(data)} documents. Processing...")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Remove MongoDB internal IDs
        if '_id' in df.columns:
            df.drop(columns=['_id'], inplace=True)
            
        # Optional: Drop other internal/technical fields if not needed
        # df.drop(columns=['merged_from_docs', 'merge_level', 'merge_rule', 'merged_upcs'], errors='ignore', inplace=True)
        
        # Reorder columns to put interesting ones first
        base_cols = ['BRAND', 'ITEM', 'Markets', 'Facts', 'NRMSIZE', 'UPC']
        other_cols = [col for col in df.columns if col not in base_cols]
        # Sort month/year columns if possible, but for now just append
        df = df[base_cols + other_cols]
        
        # Export to Excel
        print(f"Exporting to {output_file}...")
        df.to_excel(output_file, index=False)
        
        print("Done! Data exported successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    export_sales_value_to_excel()
