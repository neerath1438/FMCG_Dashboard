import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from backend.processor import normalize_item_llm
import json

items = [
    "BIOGREEN O`SOY CRACKER 16X30GM",
    "BIOGREEN O'SOY CRACKERS 16X30G"
]

results = []
for item in items:
    print(f"Processing: {item}")
    result = normalize_item_llm(item)
    results.append({
        "original": item,
        "result": result
    })

with open("biogreen_norm_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
