from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
client = MongoClient(os.getenv('MONGO_URI'))
db = client['fmcg_mastering']

# Get all 7-Eleven GTINs
seven_col = db['7-eleven_data']
all_gtins = set(str(g).strip().upper() for g in seven_col.distinct('GTIN') if g and str(g).strip() not in ['', 'NONE', 'NAN'])
print(f"Total unique 7-Eleven GTINs: {len(all_gtins)}")

# Get all carried Nielsen items (ArticleCode != NONE)
gap_col = db['7eleven_extra_items']

carried_docs = list(gap_col.find({'ArticleCode': {'$ne': 'NONE'}}, {'UPC': 1, 'ArticleCode': 1}))
print(f"Total Carried (910): {len(carried_docs)}")

# L1: Nielsen UPC directly in 7-Eleven GTIN list
l1_count = 0
l2_count = 0

for doc in carried_docs:
    upc = str(doc.get('UPC', '')).strip().upper()
    if upc in all_gtins:
        l1_count += 1
    else:
        l2_count += 1  # Carried but UPC not directly in GTIN = attribute match (L2)

print(f"\n=== Match Level Breakdown ===")
print(f"L1 (Direct UPC = GTIN match):       {l1_count}")
print(f"L2 (Attribute/merged_upcs match):   {l2_count}")
print(f"L3 (Not implemented separately):    0")
print(f"Total Carried:                      {l1_count + l2_count}")
print(f"Not Carried (Gap):                  {gap_col.count_documents({'ArticleCode': 'NONE'})}")

client.close()
