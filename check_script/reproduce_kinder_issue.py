import sys
import os
import asyncio
from difflib import SequenceMatcher
import re

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.processor import normalize_synonyms, simple_clean_item, normalize_item_llm

async def reproduce_kinder():
    item1 = "KINDER HAPPY HIPPO T5 CHOCOLATE 5X 20.7GM"
    item2 = "KINDER HAPPY HIPPO COCOA T5 20.7GX5 (103.5G)"
    
    print(f"\n--- DIAGNOSING KINDER MERGE ---")
    print(f"Item 1: {item1}")
    print(f"Item 2: {item2}")
    
    # 1. Test Synonym Normalization
    syn1 = normalize_synonyms(item1)
    syn2 = normalize_synonyms(item2)
    print(f"\n[Synonym Check]")
    print(f"Norm 1: {syn1}")
    print(f"Norm 2: {syn2}")
    
    # 2. Test Simple Clean (what fuzzy logic uses)
    clean1 = simple_clean_item(item1)
    clean2 = simple_clean_item(item2)
    print(f"\n[Cleaning Check]")
    print(f"Clean 1: {clean1}")
    print(f"Clean 2: {clean2}")
    
    # 3. Test Similarity
    sim = SequenceMatcher(None, clean1, clean2).ratio()
    print(f"\n[Similarity Check]")
    print(f"Score: {sim:.2f}")
    
    if sim > 0.85:
        print("✅ MERGE SUCCESS (Score > 0.85)")
    else:
        print("❌ MERGE FAIL (Score <= 0.85) - This matches user report")

if __name__ == "__main__":
    asyncio.run(reproduce_kinder())
