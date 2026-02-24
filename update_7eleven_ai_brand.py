import os
import sys
import json
from pymongo import MongoClient, UpdateOne
from tqdm import tqdm
from dotenv import load_dotenv

# Add backend to path to import LLMClient
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from llm_client import flow2_client

def extract_brands_batch(descriptions):
    system_prompt = """
    Extract the clean BRAND name from 7-Eleven article descriptions.
    Return a JSON array of objects, each with one field:
    - AI_BRAND: The standardized clean brand name (e.g., 'MUNCHYS', 'COCA COLA', 'NESTLE'). 
      If no specific brand is found or it's a generic product, use 'GENERIC'.
      
    Description format examples: 
    'Hup Seng Cream Cracker 300g' -> {"AI_BRAND": "HUP SENG"}
    'Coca Cola 1.5L X12' -> {"AI_BRAND": "COCA COLA"}
    'Munchy's Lexus Chocolate 190g' -> {"AI_BRAND": "MUNCHYS"}
    """
    
    user_message = f"Extract brands from these descriptions:\n" + "\n".join([f"- {d}" for d in descriptions])
    
    try:
        response = flow2_client.chat_completion(system_prompt, user_message)
        # Clean response if it contains markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
            
        data = json.loads(response)
        # Ensure it returns a list of the same length
        if len(data) != len(descriptions):
             return [{"AI_BRAND": "GENERIC"} for _ in descriptions]
        return data
    except Exception as e:
        print(f"Error in brand extraction: {e}")
        return [{"AI_BRAND": "GENERIC"} for _ in descriptions]

def update_ai_brands():
    load_dotenv(r'backend\.env')
    
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    collection_name = "7-eleven_data"
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    
    # Get all documents
    docs = list(collection.find({}, {"_id": 1, "ArticleDescription": 1}))
    total = len(docs)
    print(f"Found {total} records to update.")
    
    batch_size = 20
    updates = []
    
    for i in tqdm(range(0, total, batch_size), desc="Extracting Brands"):
        batch = docs[i:i+batch_size]
        descriptions = [d.get("ArticleDescription", "") for d in batch]
        
        extracted = extract_brands_batch(descriptions)
        
        for idx, doc in enumerate(batch):
            brand_val = extracted[idx].get("AI_BRAND", "GENERIC")
            updates.append(UpdateOne(
                {"_id": doc["_id"]},
                {"$set": {"AI_BRAND": brand_val.upper().strip()}}
            ))
            
        # Write updates in chunks
        if len(updates) >= 100:
            collection.bulk_write(updates)
            updates = []
            
    if updates:
        collection.bulk_write(updates)
        
    print("AI_BRAND update completed.")
    client.close()

if __name__ == "__main__":
    update_ai_brands()
