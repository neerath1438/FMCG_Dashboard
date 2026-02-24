import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from backend.chatbot import process_chatbot_query

load_dotenv()

# Override MONGO_URI for local test if needed
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if "mongodb:27017" in mongo_uri:
    os.environ["MONGO_URI"] = mongo_uri.replace("mongodb:27017", "localhost:27017")

q = "top 1 selling in CHOCALATE"
print(f"TESTING QUERY: {q}")
result = process_chatbot_query(q)

print("\n--- RESULTS ---")
print(f"Query Used: {json.dumps(result.get('query_used'), indent=2)}")
print(f"Result Count: {result.get('result_count')}")
if result.get('result_count') > 0:
    first_item = result.get('data')[0]
    print(f"Top Result ITEM: {first_item.get('ITEM')}")
    sales_col = "MAT Nov'24"
    sales_val = first_item.get(sales_col)
    print(f"Top Result Sales: {sales_val}")
    print(f"Top Result Facts: {first_item.get('Facts')}")
else:
    print("STILL NO DATA FOUND")

print("\n--- ANSWER ---")
print(result.get("answer"))
