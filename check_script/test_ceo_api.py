import requests
import json

url = "http://20.0.161.242:7060/query/natural"
api_key = "aptneptun-mcp-2025-secret-key-x9k2m"

payload = {
    "query": "What is the total Sales Value for OREO?",
    "context": "Inventory"
}

headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key  # Trying x-api-key first
}

print(f"Testing URL: {url}")
try:
    # Try with x-api-key header
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # If 401/403, try Authorization header
    if response.status_code in [401, 403]:
        print("Retrying with Authorization header...")
        headers["Authorization"] = f"Bearer {api_key}"
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")
