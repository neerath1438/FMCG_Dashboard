from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fmcg_mastering"]
coll = db["master_stock_data"]

# Check for documents with missing or 0 confidence
na_conf_count = coll.count_documents({"$or": [{"llm_confidence_min": {"$exists": False}}, {"llm_confidence_min": 0}, {"llm_confidence_min": None}]})
print(f"NA_CONF: {na_conf_count}")

# Check exact brand count with current logic
distinct_brands = coll.distinct("BRAND")
filtered_brands = [b for b in distinct_brands if b and str(b).strip()]
print(f"COUNT_ALL: {len(distinct_brands)}")
print(f"COUNT_FILTERED: {len(filtered_brands)}")
print(f"SAMPLE_BRANDS: {filtered_brands[:10]}")

# Check for BRAND variations using regex
import re
na_pattern = re.compile(r'^(N/A|UNKNOWN|NULL|NONE|UNDEFINED|\s|\.|\-)$', re.IGNORECASE)
na_brands = [b for b in distinct_brands if b and na_pattern.match(str(b).strip())]
print(f"NA_BRANDS_FOUND: {na_brands}")

# Check for brands that are only numbers
num_brands = [b for b in distinct_brands if b and str(b).strip().isdigit()]
print(f"NUMERIC_BRANDS_COUNT: {len(num_brands)}")
print(f"SAMPLE_NUMERIC: {num_brands[:10]}")
