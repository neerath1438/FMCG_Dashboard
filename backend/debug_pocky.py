
import sys
import os
import asyncio
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.processor import normalize_item_llm, calculate_similarity, simple_clean_item

async def debug_pocky():
    item1 = "GLICO POCKY COOKIES & CREAM STICK 40G"
    item2 = "POCKY COOKIE&CREAM 40 GM"
    
    print(f"Testing Item 1: {item1}")
    res1 = normalize_item_llm(item1)
    print(json.dumps(res1, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    print(f"Testing Item 2: {item2}")
    res2 = normalize_item_llm(item2)
    print(json.dumps(res2, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    sig1 = simple_clean_item(item1)
    sig2 = simple_clean_item(item2)
    sim = calculate_similarity(sig1, sig2)
    
    print(f"Signature 1: {sig1}")
    print(f"Signature 2: {sig2}")
    print(f"Similarity: {sim}")

if __name__ == "__main__":
    asyncio.run(debug_pocky())
