import os
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from backend.llm_client import flow2_client

def test_config():
    print(f"Testing model: {flow2_client.deployment}")
    print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    
    system_prompt = "You are a helpful assistant."
    user_prompt = "Say hello and identify yourself."
    
    try:
        response = flow2_client.chat_completion(system_prompt, user_prompt)
        print(f"Response: {response}")
        if response and response != '{}':
            print("Configuration verified successfully!")
        else:
            print("Configuration failed: Empty response")
    except Exception as e:
        print(f"Configuration failed with error: {e}")

if __name__ == "__main__":
    test_config()
