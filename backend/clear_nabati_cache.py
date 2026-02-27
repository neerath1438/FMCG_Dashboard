"""
Clear stale LLM cache entries for Nabati, Richeese, Nextar items.
This forces Flow 2 to re-call the LLM with the updated prompt/rules.
"""
from pymongo import MongoClient
import re

client = MongoClient('mongodb://localhost:27017')
db = client['fmcg_mastering']
cache_coll = db['LLM_CACHE_STORAGE']

# Match any cached item name containing these keywords
terms = ['NABATI', 'RICHEESE', 'NEXTAR']
pattern = '|'.join(terms)

result = cache_coll.delete_many({'item': {'$regex': pattern, '$options': 'i'}})
print(f"Deleted {result.deleted_count} stale cache entries for NABATI/RICHEESE/NEXTAR items.")

# Also show what's remaining related
remaining = list(cache_coll.find({'item': {'$regex': pattern, '$options': 'i'}}, {'item': 1}))
if remaining:
    print(f"WARNING: {len(remaining)} entries still remain:")
    for r in remaining:
        print(f"  - {r['item']}")
else:
    print("Cache clean for these brands.")
