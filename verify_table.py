from backend.chatbot import process_chatbot_query
import json

def verify_tabular_response():
    print("--- Testing Tabular Response Generation ---\n")
    
    question = "Pen Malaysia-ல Oreo brand items-ஓட sales value table வேணும்"
    
    print(f"Question: [Tamil Query for Oreo Sales Table]")
    response = process_chatbot_query(question)
    print(f"\nQuery Used: {json.dumps(response.get('query_used'), indent=2)}")

    
    # Check for table presence without printing raw content if it has unicode
    answer = response.get('answer', '')
    print("\n--- Answer Snippet (ASCII only) ---")
    print(answer.encode('ascii', 'ignore').decode('ascii')[:500])
    print("\n--- Answer Analysis ---")


    
    if "|" in response.get('answer') and "---" in response.get('answer'):
        print("\n[OK] Table format detected in response.")
    else:
        print("\n[FAIL] Table format NOT detected.")

if __name__ == "__main__":
    verify_tabular_response()
