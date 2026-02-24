import os
import re
import sys
import time
from difflib import SequenceMatcher
from pymongo import MongoClient
from dotenv import load_dotenv
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

# ==========================================
# Standalone Fuzzy Merge Logic (Optimized)
# ==========================================

def normalize_synonyms(text):
    """Normalize common FMCG synonyms to improve fuzzy matching."""
    if not text: return ""
    s = str(text).upper()
    syns = {
        "CHOCOLATE": ["COCOA", "CHOC", "CHOCO", "COKLAT"],
        "STRAWBERRY": ["S/BERRY", "SBERRY", "STRWB"],
        "VANILLA": ["VAN"],
        "ASSORTED": ["ASST", "ASSTD"],
        "GRAM": ["GM", "GMS", "G"],
        "BISCUIT": ["BISCUITS", "COOKIES", "COOKIE", "SNACK", "SNACKS", "STICK", "STICKS", "STIX"],
    }
    for primary, aliases in syns.items():
        for alias in aliases:
            s = re.sub(rf'\b{alias}\b', primary, s)
    return s

def simple_clean_item(name):
    """Clean item name for fuzzy signature matching."""
    if not name: return ""
    s = normalize_synonyms(str(name).upper())
    noise = ['PACK', 'PCS', 'MULTIPACK', '7ELEVEN', 'MYS']
    for n in noise:
        s = re.sub(rf'\b{n}\b', '', s)
    s = re.sub(r'[^A-Z0-9\s]', '', s)
    words = sorted(list(set(re.findall(r'[A-Z0-9]+', s))))
    return "".join(words)

def process_single_bucket(ctx_key, group):
    """Worker function to process a single context bucket."""
    local_merges = []
    if len(group) < 2:
        return local_merges

    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            d1, d2 = group[i], group[j]
            
            # Attribute Safety Lock
            f1, f2 = d1.get("flavour"), d2.get("flavour")
            p1, p2 = d1.get("product_form"), d2.get("product_form")
            
            if f1 and f2 and f1 != "UNKNOWN" and f2 != "UNKNOWN" and f1 != f2:
                continue
            if p1 and p2 and p1 != "UNKNOWN" and p2 != "UNKNOWN" and p1 != p2:
                continue

            it1, it2 = d1.get("ITEM", ""), d2.get("ITEM", "")
            sig1 = simple_clean_item(it1)
            sig2 = simple_clean_item(it2)
            
            sim = SequenceMatcher(None, sig1, sig2).ratio()
            
            if sim > 0.85:
                local_merges.append({
                    "ctx": ctx_key,
                    "sim": sim,
                    "item_a": it1,
                    "item_b": it2,
                    "id_a": d1.get("merge_id"),
                    "id_b": d2.get("merge_id")
                })
    return local_merges

def apply_fuzzy_merge_from_db():
    start_time = time.time()
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client["fmcg_mastering"]
    coll = db["master_stock_data"]

    print("\n🚀 Starting Parallel Restricted Fuzzy Merge Audit...")
    print(f"💻 Using {cpu_count()} CPU cores for speed.")
    print("-" * 50)

    # 1. Fetch Candidates (LOW_CONF Singles)
    query = {
        "llm_confidence_min": {"$lt": 0.8},
        "$or": [
            {"merge_items": {"$exists": False}},
            {"merge_items": {"$size": 1}}
        ]
    }
    
    items = list(coll.find(query))
    print(f"Found {len(items)} LOW CONFIDENCE items. Bucketing by context...")

    # 2. Bucketing
    buckets = {}
    for doc in items:
        # Important: strip _id as it's not JSON serializable for process pool
        doc.pop("_id", None)
        ctx = f"{doc.get('MARKET', 'NA')}|{doc.get('MPACK', 'NA')}|{doc.get('FACTS', 'NA')}"
        buckets.setdefault(ctx, []).append(doc)

    print(f"Created {len(buckets)} unique context buckets. Starting parallel processing...")

    # 3. Parallel Execution
    total_potential_merges = 0
    processed_buckets = 0
    valid_buckets = [b for b in buckets.items() if len(b[1]) > 1]
    total_buckets = len(valid_buckets)
    
    print(f"Starting parallel processing for {total_buckets} buckets...")

    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_single_bucket, ctx, group): ctx for ctx, group in valid_buckets}
        
        for future in as_completed(futures):
            processed_buckets += 1
            ctx_name = futures[future]
            try:
                results = future.result()
                if results:
                    # print(f"\n📦 Context: {ctx_name} - Found {len(results)} matches")
                    total_potential_merges += len(results)
                
                # Show progress every 10% or every 50 buckets
                if processed_buckets % 50 == 0 or processed_buckets == total_buckets:
                    print(f"⏳ Progress: {processed_buckets}/{total_buckets} buckets audited...")
                    
            except Exception as e:
                print(f"❌ Error processing bucket {ctx_name}: {e}")

    duration = time.time() - start_time
    print("-" * 50)
    print(f"✨ Audit Complete in {duration:.2f} seconds.")
    print(f"🔥 Total Potential Merges Found: {total_potential_merges}")

if __name__ == "__main__":
    apply_fuzzy_merge_from_db()
