import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from backend.processor import normalize_item_llm, simple_clean_item
import json

items = [
    "MUNCHYS CREAM CRACKER 300GM(25GM X 12)",
    "MUNCHYS CREAM CRACKERS 300GM(25GM X 12)"
]

results = []
for item in items:
    print(f"Processing: {item}")
    norm = normalize_item_llm(item)
    sig = simple_clean_item(item)
    results.append({
        "original": item,
        "result": norm,
        "signature": sig
    })

with open("munchys_norm_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
