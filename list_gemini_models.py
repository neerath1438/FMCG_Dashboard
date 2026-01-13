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

genai.configure(api_key=gemini_key)

try:
    print("Available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
