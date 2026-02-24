import re

def normalize_synonyms(text):
    if not text: return ""
    s = str(text).upper()
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    # ✅ Separate multipliers (e.g., 428GMX12 -> 428 GM X 12)
    s = re.sub(r'([A-Z])([X\*])', r'\1 \2', s)
    s = re.sub(r'([X\*])([A-Z])', r'\1 \2', s)
    s = re.sub(r'(\d)([X\*])', r'\1 \2', s)
    s = re.sub(r'([X\*])(\d)', r'\1 \2', s)
    syns = {
        "CHOCOLATE": ["COCOA", "CHOC", "CHOCO", "COK"],
        "GRAM": ["GM", "GMS", "G"],
        "CREAM": ["CRM", "CREME"],
        # Add more if needed from the actual file
    }
    for primary, aliases in syns.items():
        for alias in aliases:
            s = re.sub(rf'\b{alias}\b', primary, s)
    return s

def simple_clean_item(name):
    if not name: return ""
    s = str(name).upper().replace("-", "")
    s = normalize_synonyms(s)
    for word in ["ITEM", "PACK", "FLAVOUR", "FLV", "BRAND"]:
        s = s.replace(word, " ")
    words = sorted(list(set(re.findall(r'[A-Z0-9]+', s))))
    return "".join(words)

import json

items = [
    "HUP SENG CREAM CRACKER 12X428 GM",
    "HUP SENG CRM CRACKER 428GMX12"
]

results = []
for item in items:
    clean = simple_clean_item(item)
    results.append({
        "original": item,
        "cleaned": clean
    })

with open("test_cleaning_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

if __name__ == "__main__":
    pass
