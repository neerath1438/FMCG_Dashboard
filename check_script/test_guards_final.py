import sys
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Add root to path
sys.path.append(os.getcwd())
try:
    from backend.processor import standardize_item_with_llm
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

load_dotenv('backend/.env')

def test_guards():
    items = [
        "MUNCHYS OAT KRUNCH CHIA SEED 598 GM(26GM X 23)",
        "MUNCHYS OAT KRUNCH STRAWBERRY N BLACK (MEGA VALUE) 598GM(26GM X 23)",
        "SKINNY BAKERS SALTED CRMEL CHOC CHIP COOKIES 150G",
        "SKINNY BAKERS ALMOND CHOC CHIP COOKIES 150G",
        "JULIES OAT 25 STRAWBERRY +OLIGO 200GM(25GM X 8)",
        "JULIES OAT 25 TEN GRAINS 200 GM(25GM X 8)"
    ]
    
    for item in items:
        print(f"\nItem: {item}")
        # Always re-pass through guards by calling the standardizer
        res = standardize_item_with_llm(item)
        print(f"  Brand: {res.get('brand')}")
        print(f"  Flavour: {res.get('flavour')}")
        print(f"  Variant: {res.get('variant')}")

if __name__ == "__main__":
    test_guards()
