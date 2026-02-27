
import sys
import os
from pymongo import MongoClient
from bson import ObjectId

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
import processor

def analyze_split():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    ids = [
        '69a0370dc53d37bb862f1344', # OREO WAFER ROLL LIM EDT 468G
        '69a0370dc53d37bb862f1345', # OREO WAFER ROLL 468G
        '69a0370dc53d37bb862f134d', # MINI OREO VANILLA 20.4G(POUCH)
        '69a0370dc53d37bb862f1351', # OREO MINI ORIGINAL 20.4GM
        '69a0370dc53d37bb862f134f'  # OREO RED VELVET 123.5G
    ]
    
    items = list(db['master_stock_data'].find({'_id': {'$in': [ObjectId(i) for i in ids]}}))
    
    print("--- DETAILED ATTRIBUTE ANALYSIS ---")
    for i in items:
        item = i.get('ITEM')
        print(f"\nITEM: {item}")
        print(f"  Line: {i.get('product_line')}")
        print(f"  Variant: {i.get('variant')}")
        print(f"  Flavour: {i.get('flavour')}")
        print(f"  Form: {i.get('product_form')}")
        print(f"  Size: {i.get('size')}")
        print(f"  MPACK: {i.get('MPACK')}")
        
if __name__ == "__main__":
    analyze_split()
