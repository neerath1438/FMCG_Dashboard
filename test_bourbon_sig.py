import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from backend.processor import simple_clean_item
import json

items = [
    "BOURBON BUTTER COOKIES 9PCS 100G",
    "BOURBON BUTTER COOKIES 100G"
]

results = []
for item in items:
    sig = simple_clean_item(item)
    print(f"Item: {item} -> Signature: {sig}")
    results.append({
        "item": item,
        "signature": sig
    })

identical = results[0]["signature"] == results[1]["signature"]
print(f"Signatures are identical: {identical}")

with open("bourbon_sig_result.json", "w", encoding="utf-8") as f:
    json.dump({"identical": identical, "results": results}, f, indent=2)
