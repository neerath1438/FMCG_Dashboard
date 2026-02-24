
import os
import requests
from dotenv import load_dotenv

load_dotenv("d:/FMCG_Dashboard/.env")

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_API_KEY")

if not endpoint or not key:
    print("Error: Endpoint or Key missing in .env")
    exit()

# List Deployments API
# GET {endpoint}/openai/deployments?api-version=2022-12-01
api_version = "2022-12-01" # Stable version for listing
url = f"{endpoint.rstrip('/')}/openai/deployments?api-version={api_version}"

headers = {
    "api-key": key,
    "Content-Type": "application/json"
}

try:
    print(f"Querying: {url}")
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        deployments = data.get('data', [])
        print(f"Found {len(deployments)} deployments:")
        for d in deployments:
            print(f"- Name: {d.get('id')}, Model: {d.get('model')}")
    else:
        print(f"Error Response: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
