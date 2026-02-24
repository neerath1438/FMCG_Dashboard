import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.processor import normalize_synonyms

def test():
    print("Testing Synonym Normalization...")
    words = ["STICK", "SNACK", "BISCUIT", "STICKS", "SNACKS"]
    for w in words:
        norm = normalize_synonyms(w)
        print(f"'{w}' -> '{norm}'")
        
    if normalize_synonyms("STICK") == "BISCUIT" and normalize_synonyms("SNACK") == "BISCUIT":
        print("✅ SUCCESS: Synonyms are working.")
    else:
        print("❌ FAILURE: Synonyms are NOT working.")

if __name__ == "__main__":
    test()
