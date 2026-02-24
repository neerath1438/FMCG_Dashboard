
import os
import requests
import time
import json
from dotenv import load_dotenv

load_dotenv("d:/FMCG_Dashboard/.env")

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_API_KEY")

def test_gpt5_nano():
    print("\n--- Testing Deployment: gpt-5-nano (with max_completion_tokens) ---")
    url = f"{endpoint.rstrip('/')}/openai/deployments/gpt-5-nano/chat/completions?api-version=2024-02-15-preview"
    
    headers = {
        "api-key": key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "user", "content": "What is your internal model name or version? And which OpenAI series do you belong to (e.g., o1, gpt-4o)?"}
        ],
        "max_completion_tokens": 100
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            res_data = response.json()
            content = res_data['choices'][0]['message']['content']
            print(f"SUCCESS ({end_time - start_time:.2f}s)")
            print(f"Response: {content.strip()}")
        else:
            print(f"ERROR {response.status_code}: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")

if not endpoint or not key:
    print("Missing credentials.")
else:
    test_gpt5_nano()
