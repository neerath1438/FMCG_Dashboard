import sys
import os
from pathlib import Path

# Add project root to path
root_dir = str(Path(__file__).parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from backend.processor import process_llm_mastering_flow_2

# Assuming the sheet name is 'welrsel_match' based on previous logs
# If not, it will just process whatever is in SINGLE_STOCK
sheet_name = "welrsel_match"
print(f"Starting Flow 2 mastering for sheet: {sheet_name}")
results = process_llm_mastering_flow_2(sheet_name)
print(f"Flow 2 Results: {results}")
