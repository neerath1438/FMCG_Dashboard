from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
master = db["master_stock_data"]

distinct_values = master.distinct("llm_confidence_min")
print(f"Distinct Values: {distinct_values}")

for v in distinct_values:
    count = master.count_documents({"llm_confidence_min": v})
    print(f"Value {v} (Type: {type(v).__name__}): {count}")

lt_08 = master.count_documents({"llm_confidence_min": {"$lt": 0.8}})
print(f"Count of llm_confidence_min < 0.8: {lt_08}")
