import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from processor import normalize_item_name

async def test_hur_fatt():
    test_items = [
        "HUR FATT CHOCOLATE BEAN COOKIES 150G (W12)",
        "HUR FATT CHOCOLATE BUTTER COOKIES 150G (W6)"
    ]
    
    print("Testing Hur Fatt Extraction...")
    for item in test_items:
        print(f"\nItem: {item}")
        result = await normalize_item_name(item)
        print(f"Result: {result}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_hur_fatt())
