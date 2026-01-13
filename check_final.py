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
# print(f"TESTING: {q}")
result = process_chatbot_query(q)

output = {
    "query": result.get("query_used"),
    "count": result.get("result_count"),
    "top_item": result.get("data")[0].get("ITEM") if result.get("data") else "NONE",
    "top_sales": result.get("data")[0].get("MAT Nov'24") if result.get("data") else "N/A"
}

print(json.dumps(output, indent=2))
