import asyncio
import sys
import os
from difflib import SequenceMatcher

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.llm_client import llm_client, flow2_client
from backend.processor import normalize_item_llm, normalize_synonyms

def simple_clean_item(name):
    """Fallback cleaner copied from processor.py"""
    if not name: return ""
    s = normalize_synonyms(name).upper()
    for word in ["ITEM", "PACK", "FLAVOUR", "FLV", "BRAND"]:
        s = s.replace(word, " ")
    words = sorted(list(set(re.findall(r'[A-Z0-9]+', s))))
    return "".join(words)

import re

async def diagnose_pocky():
    item1 = "GLICO BRAND POCKY CHOCO BANANA FLAVOUR 25GM"
    item2 = "GLICO CHOCO BANANA 25GM"
    
    print(f"\n--- DIAGNOSING POCKY MERGE ---")
    print(f"Item 1: {item1}")
    print(f"Item 2: {item2}")
    
    # 1. Check Fuzzy Similarity
    clean1 = simple_clean_item(item1)
    clean2 = simple_clean_item(item2)
    
    sim = SequenceMatcher(None, clean1, clean2).ratio()
    print(f"\n[Fuzzy Logic Check]")
    print(f"Similarity: {sim:.2f}")

    # 2. Check LLM Normalization (Flow 2 High Confidence Path)
    print(f"\n[LLM Normalization Check]")
    
    # Mock LLM call? No, let's call real LLM to be sure
    try:
        norm1 = normalize_item_llm(item1)
        norm2 = normalize_item_llm(item2)
        
        print("\n--- Norm 1 Result ---")
        print(f"B: {norm1.get('brand')} | L: {norm1.get('product_line')} | F: {norm1.get('product_form')} | Fl: {norm1.get('flavour')}")
        
        print("\n--- Norm 2 Result ---")
        print(f"B: {norm2.get('brand')} | L: {norm2.get('product_line')} | F: {norm2.get('product_form')} | Fl: {norm2.get('flavour')}")
        
        # Check merge compatibility
        reason = []
        def safe_upper(val):
            return str(val).upper() if val else ""

        if normalize_synonyms(safe_upper(norm1.get("brand"))) != normalize_synonyms(safe_upper(norm2.get("brand"))):
             reason.append("BRAND MISMATCH")
        
        if normalize_synonyms(safe_upper(norm1.get("product_line"))) != normalize_synonyms(safe_upper(norm2.get("product_line"))):
             # Special check for empty/unknown
             l1 = safe_upper(norm1.get("product_line"))
             l2 = safe_upper(norm2.get("product_line"))
             if l1 in ["NONE", "UNKNOWN", ""] and l2 in ["NONE", "UNKNOWN", ""]:
                 pass # Both empty is fine
             elif l1 != l2:
                 reason.append(f"LINE MISMATCH ('{l1}' vs '{l2}')")

        if normalize_synonyms(safe_upper(norm1.get("product_form"))) != normalize_synonyms(safe_upper(norm2.get("product_form"))):
             f1 = normalize_synonyms(safe_upper(norm1.get("product_form")))
             f2 = normalize_synonyms(safe_upper(norm2.get("product_form")))
             reason.append(f"FORM MISMATCH ('{f1}' vs '{f2}') | Raw: '{norm1.get('product_form')}' vs '{norm2.get('product_form')}'")

        if normalize_synonyms(safe_upper(norm1.get("flavour"))) != normalize_synonyms(safe_upper(norm2.get("flavour"))):
             reason.append(f"FLAVOUR MISMATCH ('{norm1.get('flavour')}' vs '{norm2.get('flavour')}')")
             
        if not reason:
             print("\n LLM MERGE SHOULD SUCCESS!")
        else:
             print(f"\n LLM MERGE WILL FAIL: {', '.join(reason)}")

    except Exception as e:
        print(f"LLM Error: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_pocky())
