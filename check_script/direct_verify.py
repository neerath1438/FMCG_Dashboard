import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load env
env_path = Path('backend/.env')
if not env_path.exists():
    env_path = Path('.env')
load_dotenv(env_path)

api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

print(f"Key: {api_key[:5]}...{api_key[-5:]}")
print(f"Endpoint: {endpoint}")
print(f"Deployment: {deployment}")
print(f"Version: {version}")

client = AzureOpenAI(
    api_key=api_key,
    api_version=version,
    azure_endpoint=endpoint
)

try:
    resp = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
    print("Success!")
    print(resp.choices[0].message.content)
except Exception as e:
    print(f"DIRECT ERROR: {e}")
