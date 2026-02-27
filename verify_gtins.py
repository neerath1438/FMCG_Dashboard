from pymongo import MongoClient
import re

client = MongoClient('mongodb://localhost:27017/')
db = client['fmcg_mastering']
coll_master = db['master_stock_data']

# GTINs provided by the user
gtins_to_check = [
    "9556121002344", "9556121020362", "9556121020348", "9556121021123",
    "9556121020171", "2000000368726", "2000000368733", "9556121026883",
    "9556121026876", "9556121026685", "9556121026678", "9556121027057",
    "9556121026630", "9556121026623", "9556121031764"
]

print(f"{'GTIN':<15} | {'Found':<5} | {'Master Item':<40}")
print("-" * 65)

for gtin in gtins_to_check:
    # Try exact match
    doc = coll_master.find_one({"UPC": gtin})
    if not doc:
        # Try cleaning leading zeros
        gtin_clean = re.sub(r"^0+", "", gtin)
        # Search for UPCs ending with this or containing this
        doc = coll_master.find_one({"UPC": {"$regex": f"{gtin_clean}$"}})
    
    if doc:
        print(f"{gtin:<15} | YES   | {doc.get('ITEM', 'N/A')}")
    else:
        print(f"{gtin:<15} | NO    | -")
