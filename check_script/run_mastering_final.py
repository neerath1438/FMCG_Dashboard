import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

def rerun_mastering():
    load_dotenv(r"backend\.env")
    
    # We trigger Flow 2 via the API endpoint
    url = "http://localhost:8000/process/llm-mastering/Nielsen_Wersel_Test"
    
    print(f"Triggering Flow 2 Mastering: {url}")
    try:
        response = requests.post(url, timeout=600)
        if response.status_code == 200:
            print("✅ Flow 2 Completed Successfully.")
            print(response.json())
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    rerun_mastering()
