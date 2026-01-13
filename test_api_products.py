import requests
import json

try:
    resp = requests.get("http://localhost:8000/dashboard/products")
    data = resp.json()
    print(f"Products Count from API: {len(data)}")
    if data:
        print(f"First product sample: {json.dumps(data[0], indent=2)}")
except Exception as e:
    print(f"Error connecting to API: {e}")
