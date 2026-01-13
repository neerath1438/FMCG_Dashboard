import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath("backend") if os.path.exists("backend") else os.getcwd())

from backend.database import get_collection

tgt_coll = get_collection("MASTER_STOCK")
docs = list(tgt_coll.find({}))

print(f"Total Rows: {len(docs)}")

groups = {}
for d in docs:
    name = d.get("ITEM")
    fact = d.get("Facts")
    groups.setdefault(name, []).append(fact)

for name, facts in groups.items():
    print(f"\nProduct: {name}")
    print(f"Facts Count: {len(facts)}")
    for f in sorted(list(set(facts))):
        count = facts.count(f)
        print(f" - {f} ({count} row)")

# Check merge
for d in docs:
    if len(d.get("merged_upcs", [])) > 1:
        print(f"\nMERGE VERIFIED: {d.get('ITEM')} | Fact: {d.get('Facts')} | UPCs: {len(d.get('merged_upcs'))}")
        break
