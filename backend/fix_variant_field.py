"""One-off script to fix the variant field description in processor.py prompt."""
import re

path = r'd:\git\FMCG_Dashboard\backend\processor.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_str = '"variant": "Standardized Variant (e.g., REGULAR, SNOWY, MINI, GOLD, GOKUBOSO, FESTIVE).",'
new_str = '"variant": "Standardized Variant (e.g., REGULAR, SNOWY, MINI, GOLD, GOKUBOSO). NOTE: Do NOT use FESTIVE as variant. FESTIVE is seasonal packaging only - always output REGULAR for Nabati FESTIVE items.",'

if old_str in content:
    content = content.replace(old_str, new_str, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: variant field description fixed.")
else:
    # Try finding it
    idx = content.find('GOKUBOSO, FESTIVE')
    if idx != -1:
        print(f"Found at idx {idx}:")
        print(repr(content[idx-50:idx+80]))
    else:
        print("ERROR: Pattern not found at all.")
