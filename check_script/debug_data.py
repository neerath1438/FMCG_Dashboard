from backend.database import get_collection, MASTER_STOCK_COL
import json

def debug_data():
    master = get_collection(MASTER_STOCK_COL)
    docs = list(master.find().limit(10))
    
    report = []
    for d in docs:
        conf = d.get("llm_confidence_min")
        report.append({
            "item": d.get("ITEM"),
            "conf": conf,
            "conf_type": str(type(conf)),
            "merge_rule": d.get("merge_rule")
        })
    
    counts = {
        "na_zero_int": master.count_documents({"llm_confidence_min": 0}),
        "na_zero_float": master.count_documents({"llm_confidence_min": 0.0}),
        "na_none": master.count_documents({"llm_confidence_min": None}),
        "na_missing": master.count_documents({"llm_confidence_min": {"$exists": False}}),
        "gt_zero": master.count_documents({"llm_confidence_min": {"$gt": 0}}),
        "lt_70": master.count_documents({"llm_confidence_min": {"$lt": 70}})
    }
    
    print(json.dumps({"samples": report, "counts": counts}, indent=2))

if __name__ == "__main__":
    debug_data()
