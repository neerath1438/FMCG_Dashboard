from backend.llm_client import llm_client
from backend.chatbot import process_chatbot_query
from backend.processor import normalize_item_llm
import json

def test_migration():
    print("--- Testing Azure Claude Migration ---\n")

    # 1. Test Direct LLM Client
    print("1. Testing LLM Client Direct Call:")
    res = llm_client.chat_completion("Respond only with 'READY'", "Check status")
    print(f"Result: {res}")
    if "READY" in res:
        print("[OK] LLM Client is Active.\n")
    else:
        print("[FAIL] LLM Client Failed.\n")

    # 2. Test Attribute Extraction (Flow 2)
    print("2. Testing Attribute Extraction (Processor):")
    item_name = "GLICO POCKY CHOCO BANANA 25G"
    extraction = normalize_item_llm(item_name)
    print(f"Item: {item_name}")
    print(f"Extracted: {json.dumps(extraction, indent=2)}")
    if extraction.get('brand') == "GLICO" and extraction.get('confidence') > 0.8:
        print("[OK] Attribute Extraction is Correct.\n")
    else:
        print("[FAIL] Attribute Extraction Failed.\n")

    # 3. Test Chatbot Query (Flow 3)
    print("3. Testing Chatbot Query (Chatbot):")
    query = "What brands are in the database?"
    response = process_chatbot_query(query)
    print(f"Query: {query}")
    print(f"Answer Sample: {response.get('answer')[:100]}...")
    if response.get('answer'):
        print("[OK] Chatbot Query is Working.\n")
    else:
        print("[FAIL] Chatbot Query Failed.\n")

if __name__ == "__main__":
    test_migration()
