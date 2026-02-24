import sys
import os
import uuid
import copy
from pymongo import MongoClient
from dotenv import load_dotenv

# Add root
sys.path.append(os.getcwd())
try:
    from backend.processor import normalize_item_llm, simple_clean_item
    print("Successfully imported normalize_item_llm")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

load_dotenv('backend/.env')

def fix_targeted_merges():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["fmcg_mastering"]
    
    # 1. Target UPCs
    target_upcs = [
        "200172907644", "200172963163", "5098532321071", # Skinny Baker
        "9556439885158", "9556439890763", "9556439890800"  # Oat Krunch
    ]
    
    print(f"Step 1: Identifying bad clusters for {len(target_upcs)} UPCs...")
    
    # Identify and delete master records that contain these UPCs
    res = db["master_stock_data"].delete_many({"merged_upcs": {"$in": target_upcs}})
    print(f"  Deleted {res.deleted_count} old master records.")
    
    # 2. Fetch single items
    upc_ints = [int(u) for u in target_upcs if u.isdigit()]
    singles = list(db["single_stock_data"].find({"UPC": {"$in": target_upcs + upc_ints}}))
    print(f"Step 2: Found {len(singles)} single items to re-process.")
    
    # 3. Standardize and Group
    groups = {}
    for s in singles:
        print(f"  Processing: {s.get('ITEM')}")
        norm = normalize_item_llm(s["ITEM"])
        s.update({
            "BRAND": norm.get("brand"),
            "flavour": norm.get("flavour"),
            "product_form": norm.get("product_form"),
            "size": norm.get("size"),
            "variant": norm.get("variant"),
            "normalized_item": norm.get("base_item")
        })
        # Grouping key: Brand + Form + Flavour + Variant + Market + Pack + Facts + Size
        key = (
            f"{s['BRAND']}|{s['product_form']}|{s['flavour']}|{s.get('variant')}|"
            f"{s.get('Markets')}|{s.get('MPACK')}|{s.get('Facts')}|{s.get('size')}"
        )
        groups.setdefault(key, []).append(s)
        
    # 4. Create New Master Clusters
    print(f"Step 3: Creating {len(groups)} new clusters...")
    for key, items in groups.items():
        base = copy.deepcopy(items[0])
        base["merge_items"] = list(set([it["ITEM"] for it in items]))
        base["merged_upcs"] = list(set([str(it["UPC"]) for it in items]))
        base["merged_from_docs"] = len(items)
        base["merge_id"] = f"{base['BRAND']}_{uuid.uuid4().hex}"
        
        # Clean Mongo ID
        if "_id" in base: del base["_id"]
        
        db["master_stock_data"].insert_one(base)
        print(f"  ✓ Created: {base.get('BRAND')} | {base.get('flavour')} | {base.get('variant')} (Items: {len(items)})")

    print("\n✅ Done. Targeted merges fixed.")

if __name__ == "__main__":
    fix_targeted_merges()
