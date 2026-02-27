from pymongo import MongoClient
import re

client = MongoClient('mongodb://localhost:27017')
db = client['fmcg_mastering']
cache_coll = db['LLM_CACHE_STORAGE']

# Match any cached item name containing Bourbon keywords
terms = ['BOURBON', 'GOKOKU', 'CEBEURE']
pattern = '|'.join(terms)

result = cache_coll.delete_many({'item': {'$regex': pattern, '$options': 'i'}})
print(f"Deleted {result.deleted_count} stale cache entries for BOURBON items.")
