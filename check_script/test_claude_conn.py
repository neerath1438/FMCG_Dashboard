import os
import requests
import json
from dotenv import load_dotenv

def test_connection():
    load_dotenv(r"d:\FMCG_Dashboard\backend\.env")
    endpoint = os.getenv("AZURE_CLAUDE_ENDPOINT")
    key = os.getenv("AZURE_CLAUDE_API_KEY")
    model = os.getenv("AZURE_CLAUDE_MODEL_NAME", "claude-sonnet-4-5")
    version = os.getenv("AZURE_CLAUDE_API_VERSION", "2023-06-01")
    
    print(f"Testing Connection to: {endpoint}")
    
    headers = {
        "x-api-key": key,
        "Content-Type": "application/json",
        "anthropic-version": version
    }
    
    payload = {
        "model": model,
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Say 'Connection Successful' if you can read this."}
        ]
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            print("✅ Response 200: " + response.json()['content'][0]['text'])
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_connection()
