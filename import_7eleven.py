import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import sys
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Add backend to path to import LLMClient
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from llm_client import flow2_client

def extract_attributes_batch(descriptions):
    system_prompt = f"""
    You are an AI Data Architect specializing in FMCG Product Mastering. Your goal is to extract logical attributes from any Malaysian 7-Eleven description with universal adaptability.

    ### INTELLIGENT EXTRACTION RULES (General):
    1. ArticleDescription_clean: Brand + Core Product Name ONLY.
       - LOGIC: Identify the Primary Brand and the Base Product. Remove ALL secondary details (flavors, textures, series, weights, packs).
       - CLEANUP: If a word is extracted into any other field, it MUST be removed from this field.
    2. 7E_Nrmsize (UPPERCASE): Standardize Weights/Volume.
       - LOGIC: Find the numerical quantity + unit (G, ML, KG, L). Example: "130g" or "130 g" -> "130G".
    3. 7E_MPack (UPPERCASE): Multi-count Format "X<n>". Default: "X1".
       - LOGIC: Detect counts like "10s", "10x", "Bundle of 2", "Pack of 5". 
    4. 7E_Variant (UPPERCASE): Series/Sub-brand Logic.
       - LOGIC: Extract terms that define a premium tier, series, or staging (e.g., Chunky, Luxury, Original Series, Gold).
    5. 7E_product_form (UPPERCASE): Physical Category.
       - LOGIC: Identify the physical state (BISCUITS, WAFER, CRACKERS, CHIPS, STICK, ROLL, CAKE, DRINK, GUMMY).
    6. 7E_flavour (UPPERCASE): Taste Profile & Translation.
       - SEMANTIC RULE: Any word describing a TASTE or INGREDIENT flavour must be extracted here.
       - UNIVERSAL TRANSLATION: Automatically detect and translate ALL local/Malaysian flavor terms to English (e.g., Ayam -> CHICKEN, Pedas -> SPICY, Udang -> PRAWN). Do NOT rely only on lists; use your internal knowledge of the language.
       - FUZZY MATCHING: Correct minor spelling errors (e.g., "Choclate" -> "CHOCOLATE", "Biscut" -> "BISCUIT").

    ### DIVERSE EXAMPLES (For Pattern Matching):
    - "Twisties Corn Snack Chicken 60g" -> {{"ArticleDescription_clean": "Twisties", "7E_Nrmsize": "60G", "7E_MPack": "X1", "7E_Variant": "NONE", "7E_product_form": "SNACK", "7E_flavour": "CHICKEN"}}
    - "Miaow Miaow Mas Udang 50g" -> {{"ArticleDescription_clean": "Miaow Miaow", "7E_Nrmsize": "50G", "7E_MPack": "X1", "7E_Variant": "NONE", "7E_product_form": "SNACK", "7E_flavour": "PRAWN"}}
    - "Oreo Mini Choclate Cookie 20.4g 10s" -> {{"ArticleDescription_clean": "Oreo", "7E_Nrmsize": "20.4G", "7E_MPack": "X10", "7E_Variant": "MINI", "7E_product_form": "COOKIES", "7E_flavour": "CHOCOLATE"}}

    STRICT: Return a JSON array of {len(descriptions)} objects.
    """
    
    user_message = f"Extract from these descriptions:\n" + "\n".join([f"- {d}" for d in descriptions])
    
    try:
        response = flow2_client.chat_completion(system_prompt, user_message)
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                response = parts[1].strip()
            else:
                response = response.strip()
            
        return json.loads(response)
    except Exception as e:
        print(f"Error in extraction: {e}")
        return []

def get_711_cache(collection, article_description):
    doc = collection.find_one({"article_description": article_description}, {"_id": 0, "result": 1})
    return doc["result"] if doc else None

def save_711_cache(collection, article_description, result):
    # Ensure no empty values or unexpected keys
    clean_result = {k: v for k, v in result.items() if k != 'article_description'}
    collection.update_one(
        {"article_description": article_description},
        {"$set": {
            "article_description": article_description,
            "result": clean_result,
            "cached_at": datetime.utcnow().isoformat(),
        }},
        upsert=True,
    )

def import_7eleven_data():
    load_dotenv()
    
    excel_path = r'd:\git\FMCG_Dashboard\backend\Wersel_7E_Data.xlsx'
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    collection_name = "7-eleven_data"
    
    print(f"Reading Excel: {excel_path}...")
    df = pd.read_excel(excel_path)
    df.columns = [c.strip() for c in df.columns]
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    cache_collection = db["7-eleven_llm_cache"]
    
    print(f"Clearing collection {collection_name}...")
    collection.delete_many({})
    
    total = len(df)
    batch_size = 10
    num_batches = (total + batch_size - 1) // batch_size
    
    print(f"Processing {total} items in batches of {batch_size}...")

    def process_and_insert_batch(batch_idx):
        start = batch_idx * batch_size
        end = min(start + batch_size, total)
        batch_df = df.iloc[start:end]
        descriptions = batch_df['ArticleDescription'].tolist()
        
        final_extracted = {}
        to_extract = []
        
        for d in descriptions:
            cached = get_711_cache(cache_collection, d)
            if cached:
                final_extracted[d] = cached
            else:
                to_extract.append(d)
        
        if to_extract:
            extracted_list = extract_attributes_batch(to_extract)
            
            # Map by index if the LLM didn't return article_description correctly
            for i, res in enumerate(extracted_list):
                # Safely get the original description for this index
                original_d = to_extract[i] if i < len(to_extract) else None
                if not original_d: continue
                
                # Cleanup result for cache
                res_clean = {k: v for k, v in res.items() if k != 'article_description'}
                
                # Save to memory and cache
                final_extracted[original_d] = res_clean
                save_711_cache(cache_collection, original_d, res_clean)
        
        batch_docs = []
        for row in batch_df.to_dict(orient='records'):
            d = row.get('ArticleDescription')
            ext_data = final_extracted.get(d, {
                "7E_Nrmsize": "NONE", "7E_MPack": "X1", "7E_Variant": "NONE",
                "7E_product_form": "NONE", "7E_flavour": "NONE", "ArticleDescription_clean": d
            })
            row.update(ext_data)
            batch_docs.append(row)
        
        if batch_docs:
            collection.insert_many(batch_docs)
            print(f"✅ Batch {batch_idx + 1}/{num_batches} Inserted into 7-eleven_data and Cache.")

    # Use max_workers=3 for stability during cache population
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(process_and_insert_batch, range(num_batches))
    
    print(f"Import completed successfully. Total records: {total}")
    client.close()

if __name__ == "__main__":
    import_7eleven_data()
