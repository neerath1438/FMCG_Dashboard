import sys
import os
import asyncio
import re

# Add project root to path
sys.path.append(os.getcwd())

from backend.processor import normalize_mpack, normalize_item_llm, simple_clean_item

async def test_bourbon():
    items = [
        "Bourbon Gokoku No Biscuit – 133 g",
        "Bourbon Gokoku No Biscut 32P 133 g",
        "Bourbon Gokoku No Biscuit 133 g",
        "Bourbon Cebeure – 112 g",
        "Bourbon Cebeure (14 × 8 g) 112 g",
        "Bourbon Cebeure 112 g"
    ]
    
    print(f"{'ITEM':<40} | {'MPACK':<6} | {'BRAND':<10} | {'LINE':<20} | {'KEY'}")
    print("-" * 100)
    
    for item in items:
        # Extract MPACK from original item string (simplified for test)
        # In actual code it comes from Excel, here we simulate common cases
        mpack_raw = "1"
        if "32P" in item: mpack_raw = "32P"
        if "14 X 8 G" in item.upper(): mpack_raw = "(14 X 8 G)"
        
        mpack_val = normalize_mpack(mpack_raw)
        norm = normalize_item_llm(item)
        
        llm_brand = str(norm.get("brand", "UNKNOWN")).upper()
        llm_line = str(norm.get("product_line", "")).strip().upper()
        llm_form = str(norm.get("product_form", "UNKNOWN")).upper()
        llm_flavour = str(norm.get("flavour", "UNKNOWN")).upper()
        llm_variant = str(norm.get("variant", "REGULAR")).upper()
        market_val = "MALAYSIA" # Dummy
        is_sf = "REG"
        size = norm.get('size', 'UNKNOWN')
        
        if norm.get("confidence", 0) >= 0.92:
            pre_group_key = (
                f"HI_CONF|{llm_brand}|{llm_line}|{llm_form}|{llm_flavour}|{llm_variant}|{is_sf}|"
                f"{market_val}|{mpack_val}|{size}"
            )
        else:
            clean_sig = simple_clean_item(item)
            pre_group_key = (
                f"LOW_CONF|{llm_brand}|{clean_sig}|"
                f"{market_val}|{mpack_val}|{size}"
            )
            
        print(f"{item[:40]:<40} | {mpack_val:<6} | {llm_brand:<10} | {llm_line:<20} | {pre_group_key}")

if __name__ == "__main__":
    asyncio.run(test_bourbon())
