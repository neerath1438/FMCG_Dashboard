import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import sys
import json
from pathlib import Path

# Add backend to path to import LLMClient
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from llm_client import flow2_client

def extract_attributes_batch(descriptions):
    system_prompt = """
    Extract product attributes from 7-Eleven article descriptions.
    Return a JSON array of objects, each with:
    - 7E_Nrmsize: The normalized size (e.g., '300G', '500ML', '1.5L'). If not found, 'NONE'.
    - 7E_MPack: The pack count (e.g., 'X1', 'X6', 'X12'). Default to 'X1'.
    - 7E_Variant: The product variant/flavor (e.g., 'CHOCOLATE', 'ORIGINAL'). If not found, 'NONE'.

    Description format examples: 
    'Hup Seng Cream Cracker 300g' -> {"7E_Nrmsize": "300G", "7E_MPack": "X1", "7E_Variant": "CREAM"}
    'Coca Cola 1.5L X12' -> {"7E_Nrmsize": "1.5L", "7E_MPack": "X12", "7E_Variant": "ORIGINAL"}
    """
    
    user_message = f"Extract from these descriptions:\n" + "\n".join([f"- {d}" for d in descriptions])
    
    try:
        response = flow2_client.chat_completion(system_prompt, user_message)
        # Clean response if it contains markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
            
        return json.loads(response)
    except Exception as e:
        print(f"Error in extraction: {e}")
        return [{"7E_Nrmsize": "NONE", "7E_MPack": "X1", "7E_Variant": "NONE"} for _ in descriptions]

def import_7eleven_data():
    load_dotenv()
    
    excel_path = r'd:\git\FMCG_Dashboard\backend\Wersel_7E_Data.xlsx'
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    collection_name = "7-eleven_data"
    
    print(f"Reading Excel: {excel_path}...")
    df = pd.read_excel(excel_path)
    
    # Ensure column names match
    # Expected: ArticleCode, GTIN, Article_Description
    # Clean column names (strip spaces)
    df.columns = [c.strip() for c in df.columns]
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    
    # Clear existing data for a fresh import
    print(f"Clearing collection {collection_name}...")
    collection.delete_many({})
    
    total = len(df)
    batch_size = 10
    results = []
    
    print(f"Processing {total} items in batches of {batch_size}...")
    
    from concurrent.futures import ThreadPoolExecutor
    
    def process_batch(batch_idx):
        start = batch_idx * batch_size
        end = min(start + batch_size, total)
        batch_df = df.iloc[start:end]
        descriptions = batch_df['ArticleDescription'].tolist()
        
        print(f"Processing batch {batch_idx + 1}/{(total+batch_size-1)//batch_size}...")
        extracted = extract_attributes_batch(descriptions)
        
        batch_results = []
        for idx, row in enumerate(batch_df.to_dict(orient='records')):
            ext_data = extracted[idx] if idx < len(extracted) else {"7E_Nrmsize": "NONE", "7E_MPack": "X1", "7E_Variant": "NONE"}
            row.update(ext_data)
            batch_results.append(row)
        return batch_results

    num_batches = (total + batch_size - 1) // batch_size
    
    # Use max_workers=5 to avoid excessive rate limits but provide significant speedup
    with ThreadPoolExecutor(max_workers=5) as executor:
        all_results = list(executor.map(process_batch, range(num_batches)))
    
    # Flatten and insert
    final_docs = [doc for batch in all_results for doc in batch]
    if final_docs:
        collection.insert_many(final_docs)
    
    print(f"Import completed successfully. Inserted {len(final_docs)} records.")
    
    print("Import completed successfully.")
    client.close()

if __name__ == "__main__":
    import_7eleven_data()
