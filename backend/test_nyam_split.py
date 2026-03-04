
import sys
import os

# Add the project root (parent of backend) to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from backend import processor

def test_nyam_split():
    items = [
        "NYAM NYAM FANTASY STICK CHOCO 25G",
        "ARNOTTS NYAM NYAM CREAMY CHOCOLATE 25 GM",
        "NYAM NYAM FANTASY STICK CHOCO 25GM",
        "NYAM NYAM FANTASY STICK SPA CHOCO 25GM"
    ]
    
    print("--- NYAM NYAM SPLIT VERIFICATION ---")
    
    results = []
    for item in items:
        # We simulate the LLM output as generic to test the rule guards
        mock_data = {
            "brand": "ARNOTTS",
            "product_line": "NYAM NYAM",
            "flavour": "CHOCOLATE",
            "variant": "REGULAR",
            "size": "25G",
            "product_form": "SNACK",
            "confidence": 1.0
        }
        
        # Apply the guards
        output = processor.apply_llm_rule_guards(item, mock_data)
        results.append((item, output['product_line']))
        print(f"ITEM: {item}")
        print(f"  RESULT LINE: {output['product_line']}")
        print("-" * 20)

    # Validation
    fantasy_lines = [res[1] for res in results if "FANTASY STICK" in res[0]]
    creamy_line = [res[1] for res in results if "CREAMY CHOCOLATE" in res[0]][0]
    
    all_fantasy_same = len(set(fantasy_lines)) == 1
    fantasy_diff_from_creamy = creamy_line not in fantasy_lines
    
    print(f"\nVerification Results:")
    print(f"1. All Fantasy Stick items share same line: {'PASS' if all_fantasy_same else 'FAIL'}")
    print(f"2. Creamy Chocolate is separate from Fantasy Stick: {'PASS' if fantasy_diff_from_creamy else 'FAIL'} (Line: {creamy_line})")

    if all_fantasy_same and fantasy_diff_from_creamy:
        print("\n✅ VERIFICATION SUCCESSFUL!")
    else:
        print("\n❌ VERIFICATION FAILED!")

if __name__ == "__main__":
    test_nyam_split()
