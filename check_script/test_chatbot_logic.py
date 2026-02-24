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

test_questions = [
    "top 1 selling in CHOCALATE",
    "List some products",
    "Show me brands available",
    "How many items are in the master stock?",
    "Show me products for brand 'MAMEE'",
]


for q in test_questions:
    print(f"\n{'='*20}")
    print(f"QUESTION: {q}")
    result = process_chatbot_query(q)
    print(f"QUERY USED: {json.dumps(result.get('query_used'), indent=2)}")
    print(f"RESULT COUNT: {result.get('result_count')}")
    if result.get('result_count') > 0:
        print(f"SAMPLE DATA: {json.dumps(result.get('data')[0], indent=2)}")
    else:
        print("NO DATA FOUND")
    print(f"{'='*20}")

