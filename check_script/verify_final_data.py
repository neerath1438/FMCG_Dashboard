from backend.database import get_collection, MASTER_STOCK_COL
import json

def verify():
    master = get_collection(MASTER_STOCK_COL)
    total = master.count_documents({})
    na_count = master.count_documents({"llm_confidence_min": {"$in": [0, None]}})
    low_conf = master.count_documents({"llm_confidence_min": {"$gt": 0, "$lt": 70}})
    high_conf = master.count_documents({"llm_confidence_min": {"$gte": 70}})
    
    # Check top merges
    top_merges = list(master.find({"merged_from_docs": {"$gt": 1}}).sort("merged_from_docs", -1).limit(5))
    
    print(f"--- Verification Report ---")
    print(f"Total Master Records: {total}")
    print(f"N/A Confidence: {na_count} (Should be near 0)")
    print(f"Low Confidence: {low_conf}")
    print(f"High Confidence: {high_conf}")
    
    print("\n--- Sample Top Merges ---")
    for doc in top_merges:
        print(f"Item: {doc.get('ITEM')} | Brand: {doc.get('brand')} | Merged From: {doc.get('merged_from_docs')} docs")

if __name__ == "__main__":
    verify()
