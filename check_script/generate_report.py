from backend.database import get_collection, MASTER_STOCK_COL
import json

def verify():
    master = get_collection(MASTER_STOCK_COL)
    stats = {
        "total": master.count_documents({}),
        "na_count": master.count_documents({"llm_confidence_min": {"$in": [0, None]}}),
        "low_conf": master.count_documents({"llm_confidence_min": {"$gt": 0, "$lt": 70}}),
        "high_conf": master.count_documents({"llm_confidence_min": {"$gte": 70}}),
        "total_merged": master.count_documents({"merged_from_docs": {"$gt": 1}})
    }
    
    with open("verification_report.json", "w") as f:
        json.dump(stats, f)
    print("Report generated: verification_report.json")

if __name__ == "__main__":
    verify()
