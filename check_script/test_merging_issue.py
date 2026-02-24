from backend.processor import normalize_item_llm
import json

def test_normalization():
    items = [
        "GLICO BRAND POCKY CHOCO BANANA FLAVOUR 25GM",
        "GLICO CHOCO BANANA 25GM"
    ]
    
    print("--- Normalization Test ---")
    results = []
    for item in items:
        res = normalize_item_llm(item)
        results.append(res)
        print(f"Item: {item}")
        print(f"Result: {json.dumps(res, indent=2)}")
        print("-" * 20)

    # Check if they would group together
    # Key in Flow 2: brand | flavour | market | mpack | facts
    # Let's assume market=Malaysia, mpack=X1, facts=Sales Value
    
    keys = []
    for res in results:
        key = f"{res.get('brand')}|{res.get('flavour')}"
        keys.append(key)
    
    print(f"\nGrouping Keys (Brand|Flavour):")
    print(f"Item 1: {keys[0]}")
    print(f"Item 2: {keys[1]}")
    
    if keys[0] == keys[1]:
        print("\n[OK] Items would MERGE.")
    else:
        print("\n[FAIL] Items would NOT MERGE.")

if __name__ == "__main__":
    test_normalization()
