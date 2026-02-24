import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from backend.processor import normalize_item_llm

items = [
    "JULIE CHEESE STICKS 4.5KG",
    "JULIES CHEESE STICKS 4.5KG",
    "HUP SENG CREAM CRACKER 12X428 GM",
    "HUP SENG CRM CRACKER 428GMX12"
]

results = []
for item in items:
    print(f"Processing: {item}")
    result = normalize_item_llm(item)
    results.append({
        "original": item,
        "result": result
    })

import json
with open("julie_norm_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
