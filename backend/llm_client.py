import os
import requests
import json
from openai import OpenAI
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend directory OR parent directory
current_dir = Path(__file__).parent
env_path = current_dir / '.env'
if not env_path.exists():
    env_path = current_dir.parent / '.env'

class LLMClient:
    def __init__(self):
        self.use_azure = True
        self.azure_endpoint = os.getenv("AZURE_CLAUDE_ENDPOINT")
        self.azure_key = os.getenv("AZURE_CLAUDE_API_KEY")
        self.azure_model = os.getenv("AZURE_CLAUDE_MODEL_NAME", "claude-sonnet-4-5")

        # Fallback OpenAI
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=httpx.Client()
        )

    def chat_completion(self, system_prompt, user_message, temperature=0, max_tokens=1000):
        if self.use_azure and self.azure_endpoint and self.azure_key:
            try:
                headers = {
                    "x-api-key": self.azure_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
                payload = {
                    "model": self.azure_model,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_message}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                response = requests.post(self.azure_endpoint, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    res_json = response.json()
                    # Anthropic response format: res['content'][0]['text']
                    return res_json['content'][0]['text']
                else:
                    print(f"Azure Claude Error: {response.status_code} - {response.text}")
                    # Fallback to OpenAI if Azure fails
            except Exception as e:
                print(f"Azure Claude Exception: {e}")

        # Fallback to OpenAI
        try:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error: All AI models failed. {str(e)}"

# Singleton instance
llm_client = LLMClient()
