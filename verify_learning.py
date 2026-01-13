from backend.chatbot import process_chatbot_query, get_learning_context
from backend.database import get_collection
import json

def verify_learning_loop():
    print("--- Testing Smart Learning Loop ---\n")
    
    learning_coll = get_collection("CHATBOT_LEARNING")
    history_coll = get_collection("CHATBOT_HISTORY")
    
    # 1. Clear previous test data
    learning_coll.delete_many({"test_id": "test_loop"})
    history_coll.delete_many({"question": "TEST_QUESTION_123"})

    test_question = "TEST_QUESTION_123"
    test_correction = {"ITEM": "CORRECTED_RESULT"}

    # 2. Add a 'Mock' Correction
    print(f"1. Adding Correction for: {test_question}")
    learning_coll.insert_one({
        "test_id": "test_loop",
        "question": test_question,
        "correction": test_correction
    })

    # 3. Verify Learning Context reflects the change
    print("2. Checking Learning Context...")
    context = get_learning_context()
    if test_question in context and "CORRECTED_RESULT" in context:
        print("[OK] Learning Context updated with correction.")
    else:
        print("[FAIL] Learning Context missing correction.")
        return

    # 4. Run Chatbot and check History Logging
    print(f"3. Running Chatbot Query: {test_question}")
    process_chatbot_query(test_question)
    
    log = history_coll.find_one({"question": test_question})
    if log:
        print("[OK] Interaction logged to CHATBOT_HISTORY.")
    else:
        print("[FAIL] Interaction NOT logged.")

    # Cleanup
    learning_coll.delete_many({"test_id": "test_loop"})
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_learning_loop()
