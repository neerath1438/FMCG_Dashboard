from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

client = MongoClient(os.getenv('MONGO_URI'))
col = client['fmcg_mastering']['master_stock_data']
docs = list(col.find({'BRAND': {'$regex': 'SKINNY BAKER', '$options': 'i'}}))
print(f'Total Skinny Baker clusters: {len(docs)}')
for d in docs:
    items = d.get('merge_items', [d.get('ITEM')])
    print(f'FL:{d.get("flavour")} | VR:{d.get("variant")} | items:{len(items)}')
    for it in items:
        print(f'  {str(it)[:80]}')
client.close()
