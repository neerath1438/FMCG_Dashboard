from backend.chatbot import process_chatbot_query
import json

def verify_technical_query():
    print("--- Testing Technical Query Processing ---\n")
    
    question = 'enaku ipom db.MASTER_STOCK.find( { BRAND:"OREO","merged_upcs.1": { "$exists": true } }, { "ITEM": 1, "merged_upcs":1, "_id": 0, "merge_items":1, "Facts":1, "Markets":1 } ).count() intha query excecute pani kudu'
    
    print(f"Question: {question}")
    response = process_chatbot_query(question)
    
    print(f"\nAnswer: {response.get('answer').encode('ascii', 'ignore').decode('ascii')}")
    print(f"Query Used: {json.dumps(response.get('query_used'), indent=2)}")
    print(f"Result Count: {response.get('result_count')}")
    print(f"Explanation: {response.get('explanation').encode('ascii', 'ignore').decode('ascii')}")


    if response.get('result_count') > 0 or "OREO" in response.get('answer'):
        print("\n[OK] Technical Query Processed Successfully.")
    else:
        print("\n[FAIL] Technical Query Failed.")

if __name__ == "__main__":
    verify_technical_query()
