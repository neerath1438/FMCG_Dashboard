import os
import json
import asyncio
import sys
from pathlib import Path

# Add backend to path to import LLMClient and processor logic
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from processor import normalize_item_llm, LLM_CONFIDENCE_THRESHOLD, simple_clean_item

# Mock/Test items provided by the user
test_items = [
    "MUNCHYS LEXUS F/PACK CHOCOLATE SANDWICH 190 GM(19GM X 10)",
    "BONTEMPS COOKIES PNUT 380GM",
    "FAZ CHIA SEED CHOCOLATE CHIP COOKIES 90G",
    "ARNOLD'S TIM TAM SALT CARAMEL BROWNIE",
    "DODONI CARAMELISED ONION",
    "LOACKER QUADRATINI PREMIUM NPLTNE",
    "OREO DARK & WHITE CHOCOLATE",
    "ALL TIME FAVOURITE ASSORTED BISCUIT",
    "ORI SALTED SAVOURY CRACKER"
]

# Mock some fields that would exist in single_stock_data
mock_docs = []
for item in test_items:
    mock_docs.append({
        "ITEM": item,
        "BRAND": "LEXUS",
        "MARKETS": "WEST MALAYSIA",
        "MPACK": "X10",
        "FACTS": "Sales Value",
        "NRMSIZE": "190G"
    })

async def run_debug_flow2():
    print("Starting Flow 2 Debug Test for Munchys Lexus...")
    print(f"Confidence Threshold: {LLM_CONFIDENCE_THRESHOLD}")
    print("-" * 50)
    
    norm_map = {}
    
    # 1. Extraction Phase
    for item in test_items:
        print(f"Processing: {item}")
        # Note: In real flow, it might prepend brand. 
        # Here we use context-aware naming if brand is missing or just the item since LEXUS is in the names.
        res = normalize_item_llm(item)
        norm_map[item] = res
        print(f"   -> Brand: {res.get('brand')}")
        print(f"   -> Flavour: {res.get('flavour')}")
        print(f"   -> Variant: {res.get('variant')}")
        print(f"   -> Confidence: {res.get('confidence')}")
        print("-" * 30)

    # 2. Grouping Phase
    print("\nGrouping Results (Master Merges):")
    pre_groups = {}
    
    for d in mock_docs:
        item = d.get("ITEM")
        norm = norm_map.get(item, {})
        
        llm_brand = str(norm.get("brand", "UNKNOWN")).upper()
        llm_form = str(norm.get("product_form", "UNKNOWN")).upper()
        llm_flavour = str(norm.get("flavour", "UNKNOWN")).upper()
        llm_variant = str(norm.get("variant", "REGULAR")).upper()
        llm_line = str(norm.get("product_line", "")).strip().upper()
        
        is_sf = "SF" if norm.get("is_sugar_free") else "REG"
        market_val = d.get("MARKETS", "UNKNOWN")
        mpack_val = d.get("MPACK", "UNKNOWN")
        facts_val = d.get("FACTS", "UNKNOWN")
        size_val = norm.get("size", "UNKNOWN")
        
        # Consistent Key logic from processor.py
        if norm.get("confidence", 0) >= LLM_CONFIDENCE_THRESHOLD:
            # FIX 3: ASSORTED Protection (Keep different Assorted names separate)
            assorted_guard = ""
            if llm_form == "ASSORTED":
                assorted_guard = f"|{simple_clean_item(item)}"
                
            pre_group_key = (
                f"HI_CONF|{llm_brand}|{llm_line}|{llm_form}|{llm_flavour}|{llm_variant}|{is_sf}|"
                f"{market_val}|{mpack_val}|{facts_val}|{size_val}{assorted_guard}"
            )
        else:
            clean_sig = simple_clean_item(item)
            pre_group_key = (
                f"LOW_CONF|{llm_brand}|{clean_sig}|"
                f"{market_val}|{mpack_val}|{facts_val}|{size_val}"
            )
            
        if pre_group_key not in pre_groups:
            pre_groups[pre_group_key] = []
        pre_groups[pre_group_key].append(item)

    # Print summary
    group_num = 1
    for key, items in pre_groups.items():
        print(f"\nGroup {group_num} (Key: {key})")
        for it in items:
            print(f"  - {it}")
        group_num += 1

if __name__ == "__main__":
    asyncio.run(run_debug_flow2())
