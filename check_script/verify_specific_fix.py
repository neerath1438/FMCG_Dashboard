import asyncio
import os
import sys

# Ensure backend is in path
sys.path.append(os.getcwd())

from backend.processor import normalize_item_llm, simple_clean_item

async def test_items():
    test_cases = [
        "HELLO PANDA DIP DIP STRAWBERRY 20G",
        "MEIJI HELLO PANDA SBERY 25GM",
        "HELLO PANDA DIP DIP CHOCOLATE 20G",
        "MEIJI HELLO PANDA CHCO 25GM",
        "NYAM NYAM BUBBLE PUFF STRAWBERRY 25G",
        "NYAM NYAM STRAWBERRY 27G"
    ]
    
    print("\n=== STARTING TARGETED LLM VERIFICATION ===\n")
    
    results = {}
    for item in test_cases:
        print(f"Processing: {item}")
        res = normalize_item_llm(item)
        results[item] = res
        print(f"  - Brand: {res.get('brand')}")
        print(f"  - Product Line: {res.get('product_line')}")
        print(f"  - Flavour: {res.get('flavour')}")
        print(f"  - Form: {res.get('product_form')}")
        print(f"  - Confidence: {res.get('confidence')}")
        print("-" * 30)

    # Verification Logic (Simplified Grouping check)
    print("\n=== MERGE GROUPING VERIFICATION ===\n")
    
    def get_group_key(item, res):
        llm_brand = str(res.get("brand", "UNKNOWN")).upper()
        llm_line = str(res.get("product_line", "NONE")).upper()
        llm_flavour = str(res.get("flavour", "UNKNOWN")).upper()
        llm_form = str(res.get("product_form", "UNKNOWN")).upper()
        
        # In processor.py, if line is missing, it downgrades to LOW_CONF
        if not llm_line or llm_line == "NONE":
            return f"LOW_CONF|{llm_brand}|{simple_clean_item(item)}"
        
        # High confidence key includes product_line
        return f"HIGH_CONF|{llm_brand}|{llm_line}|{llm_flavour}|{llm_form}"

    groups = {}
    for item, res in results.items():
        key = get_group_key(item, res)
        groups.setdefault(key, []).append(item)
    
    for key, items in groups.items():
        print(f"Group Key: {key}")
        for it in items:
            print(f"  - {it}")
        print()

    # Specific checks
    print("=== FINAL VERDICT ===")
    
    # 1. Hello Panda regular vs Dip Dip
    hp_dip_straw = results["HELLO PANDA DIP DIP STRAWBERRY 20G"]
    hp_reg_straw = results["MEIJI HELLO PANDA SBERY 25GM"]
    
    if get_group_key("HELLO PANDA DIP DIP STRAWBERRY 20G", hp_dip_straw) != get_group_key("MEIJI HELLO PANDA SBERY 25GM", hp_reg_straw):
        print("✅ SUCCESS: HELLO PANDA DIP DIP and Regular HELLO PANDA are SEPARATED.")
    else:
        print("❌ FAILURE: HELLO PANDA DIP DIP and Regular HELLO PANDA ARE MERGED!")

    # 2. Nyam Nyam regular vs Bubble Puff
    nn_bubble = results["NYAM NYAM BUBBLE PUFF STRAWBERRY 25G"]
    nn_reg = results["NYAM NYAM STRAWBERRY 27G"]
    
    if get_group_key("NYAM NYAM BUBBLE PUFF STRAWBERRY 25G", nn_bubble) != get_group_key("NYAM NYAM STRAWBERRY 27G", nn_reg):
        print("✅ SUCCESS: NYAM NYAM BUBBLE PUFF and Regular NYAM NYAM are SEPARATED.")
    else:
        print("❌ FAILURE: NYAM NYAM BUBBLE PUFF and Regular NYAM NYAM ARE MERGED!")

if __name__ == "__main__":
    asyncio.run(test_items())
