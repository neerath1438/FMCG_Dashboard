import sys
import os
import asyncio
import re

# Add project root to path
sys.path.append(os.getcwd())

from backend.processor import normalize_mpack, normalize_item_llm, simple_clean_item

async def test_lexus():
    items = [
        "LEXUS CHOCO COATED CREAM BISCUITS 200GM (10S X 20GM)",
        "LEXUS CHOCO COATED CREAM BISCUITS 200G(10X20G"
    ]
    
    print(f"{'ITEM':<60} | {'MPACK':<6} | {'BRAND':<10} | {'LINE':<20} | {'SIZE':<10} | {'KEY'}")
    print("-" * 120)
    
    for item in items:
        mpack_val = normalize_mpack("X10")
        norm = normalize_item_llm(item)
        print(f"DEBUG: norm for '{item[:20]}...' -> {norm}")
        
        # Check what clean_raw would be in processor
        from backend.processor import normalize_synonyms
        clean_raw_debug = normalize_synonyms(item).upper()
        print(f"DEBUG: clean_raw -> '{clean_raw_debug}'")
        
        llm_brand = str(norm.get("brand", "UNKNOWN")).upper()
        llm_line = str(norm.get("product_line", "")).strip().upper()
        llm_form = str(norm.get("product_form", "UNKNOWN")).upper()
        llm_flavour = str(norm.get("flavour", "UNKNOWN")).upper()
        llm_variant = str(norm.get("variant", "REGULAR")).upper()
        market_val = "PEN MALAYSIA" 
        is_sf = "REG"
        size = str(norm.get('size', 'UNKNOWN')).upper()
        
        confidence = norm.get("confidence", 0)
        
        if confidence >= 0.92:
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
            
        print(f"{item[:60]:<60} | {mpack_val:<6} | {llm_brand:<10} | {llm_line:<20} | {size:<10} | {pre_group_key}")

if __name__ == "__main__":
    asyncio.run(test_lexus())
