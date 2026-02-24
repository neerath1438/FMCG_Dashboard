import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(".env")
if not env_path.exists():
    env_path = Path("backend/.env")

load_dotenv(dotenv_path=env_path)
gemini_key = os.getenv("GEMINI_API_KEY")

print(f"Testing Gemini API Key (first 10 chars): {gemini_key[:10]}...")

if not gemini_key:
    print("FAILURE: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=gemini_key)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello, respond with 'READY'")
    print(f"✅ SUCCESS: Gemini API is working!")
    print(f"Response: {response.text}")
except Exception as e:
    print("❌ FAILURE: Gemini API is NOT working.")
    print(f"Error Details: {e}")
