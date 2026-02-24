
import os
import requests
import time
import json
from dotenv import load_dotenv

load_dotenv("d:/FMCG_Dashboard/.env")

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_API_KEY")

deployments = [
    "gpt-5-nano",
    "claude-sonnet-4-5",
    "Llama-4-Maverick-17B-128E-Instruct-FP8"
]

def test_model(deployment_name):
    print(f"\n--- Testing Deployment: {deployment_name} ---")
    # Use standard Azure OpenAI chat completion URL
    url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
    
    headers = {
        "api-key": key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Identify your model version and knowledge cutoff."},
            {"role": "user", "content": "What is your model name and knowledge cutoff?"}
        ],
        "max_tokens": 100
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            res_data = response.json()
            content = res_data['choices'][0]['message']['content']
            model_id = res_data.get('model', 'unknown')
            print(f"SUCCESS ({end_time - start_time:.2f}s)")
            print(f"Internal Model ID: {model_id}")
            print(f"Response: {content.strip()}")
        else:
            print(f"ERROR {response.status_code}: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")

if not endpoint or not key:
    print("Missing credentials.")
else:
    for d in deployments:
        test_model(d)
