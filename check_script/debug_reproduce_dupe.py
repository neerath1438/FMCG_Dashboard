
import collections
import uuid
from pymongo import UpdateOne

# Mock data
docs = [{"ITEM": f"Item_{i}", "BRAND": "BrandX", "UPC": f"UPC_{i}", "MARKETS": "Mkt", "MPACK": "1", "FACTS": "F"} for i in range(18)]

# Mock norm map
norm_map = {}
for d in docs:
    norm_map[d["ITEM"]] = {
        "brand": "BrandX",
        "product_line": "Line1",
        "confidence": 0.95,
        "product_form": "Stick",
        "flavour": "Choco",
        "is_sugar_free": False,
        "size": "100g",
        "base_item": d["ITEM"]
    }

def simple_clean_item(name):
    return name

LLM_CONFIDENCE_THRESHOLD = 0.92

def get_val(doc, keys):
    return "val"

# 1. Grouping Phase Logic (Copied from processor.py)
pre_groups = {}
for d in docs:
    item = d.get("ITEM")
    norm = norm_map.get(item)
    
    llm_brand = str(norm.get("brand", "UNKNOWN")).upper()
    llm_form = str(norm.get("product_form", "UNKNOWN")).upper()
    llm_flavour = str(norm.get("flavour", "UNKNOWN")).upper()
    
    # Mocking key generation
    pre_group_key = f"{llm_brand}|{llm_form}|{llm_flavour}"
    pre_groups.setdefault(pre_group_key, []).append(d)

final_groups_list = []
for pg_key, pg_docs in pre_groups.items():
    # Mock size logic (all same size)
    for d in pg_docs:
        d["_size_val"] = 100.0
    
    # Sort
    pg_docs.sort(key=lambda x: x["_size_val"])
    
    current_bucket = []
    for d in pg_docs:
        if not current_bucket:
            current_bucket.append(d)
            continue
        
        prev_d = current_bucket[-1]
        if abs(d["_size_val"] - prev_d["_size_val"]) <= 5.0:
            current_bucket.append(d)
        else:
            final_groups_list.append(current_bucket)
            current_bucket = [d]
    if current_bucket:
        final_groups_list.append(current_bucket)

print(f"Clusters formed: {len(final_groups_list)}")

# 2. Batch Generation Logic (Copied from processor.py)
batch_operations = []

for cluster_docs in final_groups_list:
    valid_subgroups = [cluster_docs]
    
    if len(cluster_docs) > 1:
        # Mock splitting logic
        pass

    for group_docs in valid_subgroups:
        # Sort
        group_docs.sort(key=lambda x: x.get("ITEM"))

        # Single item
        if len(group_docs) == 1:
            doc = group_docs[0].copy()
            # ... processing ...
            doc["merge_id"] = "123"
            doc["sheet_name"] = "test"
            
            batch_operations.append(f"UpdateOne Single {doc['ITEM']}")
            continue

        # Merge multiple items
        # ... processing ...
        batch_operations.append(f"UpdateOne Merge {len(group_docs)}")

print(f"Batch operations count: {len(batch_operations)}")
