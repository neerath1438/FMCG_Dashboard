import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import collections

def analyze_nielsen_duplicates():
    load_dotenv()
    
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    print("Querying Nielsen data (Facts: 'Sales Value', Market: 'Pen Malaysia')...")
    query = {
        "Facts": "Sales Value",
        "Markets": "Pen Malaysia"
    }
    
    docs = list(db["master_stock_data"].find(query))
    print(f"Total records found: {len(docs)}")
    
    if not docs:
        print("No documents found with the given query.")
        return

    # Create a dictionary to hold records by UPC
    upc_map = collections.defaultdict(list)
    for doc in docs:
        upc_map[doc.get('UPC')].append(doc)
        
    dupes = {upc: records for upc, records in upc_map.items() if len(records) > 1}
    
    print(f"Found {len(dupes)} UPCs that have multiple entries.")
    print("-" * 60)
    
    if not dupes:
        print("No duplicate UPCs found.")
        return

    report = []
    
    for upc, records in dupes.items():
        # Check for differences in key fields
        fields_to_check = ['ITEM', 'BRAND', 'MPACK', 'NRMSIZE', 'VARIANT']
        
        # Get unique values for each field
        variations = {}
        for field in fields_to_check:
            vals = set(str(r.get(field)).strip().upper() for r in records)
            if len(vals) > 1:
                variations[field] = list(vals)
        
        upc_report = {
            "UPC": upc,
            "Count": len(records),
            "Type": "EXACT DUPLICATE" if not variations else "VARIATION",
            "VaryingFields": variations
        }
        report.append(upc_report)
        
        # Print sample findings
        if len(report) <= 20: # Limit print to 1st 20
            print(f"UPC: {upc} (Count: {len(records)})")
            if not variations:
                print("  -> Result: Identical data across all entries.")
            else:
                print(f"  -> Result: Different values found in fields: {list(variations.keys())}")
                for field, vals in variations.items():
                    print(f"     - {field}: {vals}")
            print("-" * 30)

    # Summary Stats
    exact_count = sum(1 for r in report if r["Type"] == "EXACT DUPLICATE")
    variation_count = sum(1 for r in report if r["Type"] == "VARIATION")
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY REPORT")
    print("=" * 60)
    print(f"Total Duplicate UPCs: {len(dupes)}")
    print(f"Exact Duplicates (Same data): {exact_count}")
    print(f"Variations (Different Item/Attributes): {variation_count}")
    print("=" * 60)
    
    # Save detailed report to CSV for user to check
    df_report = pd.DataFrame(report)
    output_file = "nielsen_duplicate_analysis.csv"
    df_report.to_csv(output_file, index=False)
    print(f"\nDetailed report saved to: {output_file}")

if __name__ == "__main__":
    analyze_nielsen_duplicates()
