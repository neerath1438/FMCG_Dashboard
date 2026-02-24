import os
import json
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from backend.llm_client import llm_client
import time

# Load env
load_dotenv(r"backend\.env")

def get_merged_groups():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client["fmcg_mastering"]
    coll = db["master_stock_data"]
    
    # Get groups where more than 1 item is merged
    query = {"$expr": {"$gt": [{"$size": "$merge_items"}, 1]}}
    groups = list(coll.find(query))
    client.close()
    return groups

def update_cache(item, corrected_data):
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client["fmcg_mastering"]
    coll = db["LLM_CACHE_STORAGE"]
    
    coll.update_one(
        {"item": item},
        {"$set": {"result": corrected_data}},
        upsert=True
    )
    client.close()

def audit_groups(groups, dry_run=True):
    results = []
    checkpoint_file = "qa_audit_progress.json"
    processed_master_ids = []
    
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            processed_master_ids = json.load(f)
            
    total = len(groups)
    print(f"Starting Audit on {total} merged groups. Resume count: {len(processed_master_ids)}")
    
    system_prompt = """You are an expert FMCG Product auditor. 
Your task is to review a group of product items that have been merged together.
Verify if they truly belong to the same product (Same Brand, Same Flavour, Same Variant, Same Size).

If they are a CORRECT match, return: {"status": "MATCH"}

If there is an INCORRECT item in the group (Mismatch in Brand, Flavour, Variant or Size), return a list of corrections for the items in the group.
Format: 
{
  "status": "MISMATCH",
  "reason": "Brief reason for mismatch",
  "corrections": [
    {
      "item": "Original Raw Item Name",
      "brand": "Correct Brand",
      "flavour": "Correct Flavour (e.g. NORMAL, CHOCOLATE, OATS)",
      "variant": "Correct Variant (e.g. REGULAR, SUGAR FREE)",
      "size": "Correct Size (e.g. 190G)"
    }
  ]
}

Strictly return ONLY valid JSON."""

    target_dir = r"D:\master_final_reports_QA"
    if not os.path.exists(target_dir): os.makedirs(target_dir)
    output_path = os.path.join(target_dir, "QA_Mismatch_Report.xlsx")

    for i, group in enumerate(groups):
        m_id = str(group.get("_id"))
        if m_id in processed_master_ids:
            continue
            
        master_item = group.get("ITEM")
        merge_items = group.get("merge_items", [])
        
        print(f"[{i+1}/{total}] Auditing group: {master_item[:50]}...")
        
        user_message = f"Verify this merged group. Master: Brand: {group.get('BRAND')}, Flavour: {group.get('flavour')}, Variant: {group.get('variant')}, Size: {group.get('size')}\n\nItems:\n" + "\n".join(merge_items)
        
        try:
            response_text = llm_client.chat_completion(system_prompt, user_message)
            
            clean_json = response_text.strip()
            if "```json" in clean_json: clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json: clean_json = clean_json.split("```")[1].split("```")[0].strip()
                
            res = json.loads(clean_json)
            
            if res.get("status") == "MISMATCH":
                print(f"  ❌ MISMATCH Found: {res.get('reason')}")
                for corr in res.get("corrections", []):
                    item_name = corr.get("item")
                    data = {"brand": corr.get("brand"), "flavour": corr.get("flavour"), "variant": corr.get("variant"), "size": corr.get("size")}
                    results.append({"Master": master_item, "Item": item_name, "Reason": res.get("reason"), "Corrected_Data": data})
                    if not dry_run: update_cache(item_name, data)
                
                # Save incremental results to Excel
                if results:
                    pd.DataFrame(results).to_excel(output_path, index=False)
            else:
                print(f"  ✅ Group Valid.")
                
            # Update progress
            processed_master_ids.append(m_id)
            with open(checkpoint_file, "w") as f: json.dump(processed_master_ids, f)
            
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
            
        time.sleep(1.0) # Ethical spacing

    return results

def main():
    groups = get_merged_groups()
    if not groups: return
    audit_groups(groups, dry_run=False) 
    print("\nAudit Complete.")

if __name__ == "__main__":
    main()
