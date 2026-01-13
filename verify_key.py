import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Try to load .env from current dir or parent
env_path = Path(".env")
if not env_path.exists():
    env_path = Path("backend/.env")

load_dotenv(dotenv_path=env_path)
api_key = os.getenv("OPENAI_API_KEY")

print(f"Testing API Key (first 10 chars): {api_key[:10]}...")

client = OpenAI(api_key=api_key)

try:
    # Minimal test call
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    print("✅ SUCCESS: Your API Key is working perfectly!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print("FAILURE: Your API Key is NOT working.")
    if "insufficient_quota" in str(e):
        print("REASON: Insufficient Quota. You need to add credits (Balance) to your OpenAI account.")
    else:
        print(f"Error Details: {e}")

