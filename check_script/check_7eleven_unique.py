from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']

# Get counts
seven_eleven_total = db['7-eleven_data'].count_documents({})
extra_total = db['7eleven_extra_items'].count_documents({})
carried = db['7eleven_extra_items'].count_documents({'Article_Description': {'$ne': 'NOT CARRIED'}})
gaps = db['7eleven_extra_items'].count_documents({'Article_Description': 'NOT CARRIED'})

print("=" * 50)
print("7-ELEVEN DATA ANALYSIS")
print("=" * 50)
print(f"\n1. 7-eleven_data collection total: {seven_eleven_total}")
print(f"2. 7eleven_extra_items total: {extra_total}")
print(f"\n3. Carried (Article_Description != 'NOT CARRIED'): {carried}")
print(f"4. Gaps (Article_Description = 'NOT CARRIED'): {gaps}")
print(f"\n5. Carried + Gaps = {carried + gaps}")

print("\n" + "=" * 50)
print("7-ELEVEN UNIQUE CALCULATION")
print("=" * 50)
print(f"\nFormula: Total 7-Eleven - Carried Items")
print(f"Result: {seven_eleven_total} - {carried} = {seven_eleven_total - carried}")
print(f"\nHTML shows: 2,406")
print(f"Calculated: {seven_eleven_total - carried}")
