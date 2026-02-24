import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.processor import process_llm_mastering_flow_2
from backend.database import get_collection

async def test_fuzzy_merge():
    # 1. Setup Mock Items in Single Stock
    single_col = get_collection("single_stock_data")
    master_col = get_collection("master_stock_data")
    
    # Clean up previous test data if any
    brands = ["BOURBON_TEST", "KINDER_TEST"]
    single_col.delete_many({"sheet_name": "test_fuzzy_sheet", "BRAND": {"$in": brands}})
    master_col.delete_many({"sheet_name": "test_fuzzy_sheet", "BRAND": {"$in": brands}})
    
    test_items = [
        {
            "ITEM": "BOURBON LUMONDE COOKIE 93G",
            "BRAND": "BOURBON_TEST",
            "MARKETS": "Pen Malaysia",
            "MPACK": "X1",
            "FACTS": "Value",
            "UPC": "111",
            "sheet_name": "test_fuzzy_sheet"
        },
        {
            "ITEM": "BOURBON LUMOND 93G",
            "BRAND": "BOURBON_TEST",
            "MARKETS": "Pen Malaysia",
            "MPACK": "X1",
            "FACTS": "Value",
            "UPC": "222",
            "sheet_name": "test_fuzzy_sheet"
        },
        {
            "ITEM": "KINDER HAPPY HIPPO T5 CHOCOLATE 5X 20.7GM",
            "BRAND": "KINDER_TEST",
            "MARKETS": "PM MT Smkt",
            "MPACK": "X1",
            "FACTS": "Value",
            "UPC": "333",
            "sheet_name": "test_fuzzy_sheet"
        },
        {
            "ITEM": "KINDER HAPPY HIPPO COCOA T5 20.7GX5 (103.5G)",
            "BRAND": "KINDER_TEST",
            "MARKETS": "PM MT Smkt",
            "MPACK": "X1",
            "FACTS": "Value",
            "UPC": "444",
            "sheet_name": "test_fuzzy_sheet"
        }
    ]
    
    single_col.insert_many(test_items)
    print("DONE: Inserted test items into Single Stock")

    # 2. Run Flow 2
    print("START: Triggering Flow 2 processing...")
    result = await process_llm_mastering_flow_2("test_fuzzy_sheet")
    print(f"Flow 2 Result: {result}")

    # 3. Verify Master Stock
    master_records = list(master_col.find({"BRAND": {"$in": brands}, "sheet_name": "test_fuzzy_sheet"}))
    
    print(f"\nFound {len(master_records)} master records for {brands}.")
    
    for rec in master_records:
        print(f"Brand: {rec.get('BRAND')} | Items: {rec.get('merge_items')}")

    bourbon_merged = any(rec.get('BRAND') == 'BOURBON_TEST' and len(rec.get('merge_items', [])) == 2 for rec in master_records)
    kinder_merged = any(rec.get('BRAND') == 'KINDER_TEST' and len(rec.get('merge_items', [])) == 2 for rec in master_records)

    if bourbon_merged:
        print("SUCCESS: Bourbon items were merged.")
    else:
        print("FAILURE: Bourbon items were NOT merged.")

    if kinder_merged:
        print("SUCCESS: Kinder (Chocolate vs Cocoa) items were merged.")
    else:
        print("FAILURE: Kinder (Chocolate vs Cocoa) items were NOT merged.")

if __name__ == "__main__":
    asyncio.run(test_fuzzy_merge())
