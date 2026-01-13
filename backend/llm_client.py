import os
import requests
import json
import time
import re
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
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests

    def _wait_for_rate_limit(self):
        """Ensure minimum time between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def _parse_retry_after(self, error_text):
        """Extract wait time from rate limit error message"""
        try:
            # Look for "wait X seconds" pattern
            match = re.search(r'wait (\d+) second', error_text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        except:
            pass
        return None

    def chat_completion(self, system_prompt, user_message, temperature=0, max_tokens=1000):
        max_retries = 3
        base_wait_time = 5
        
        for attempt in range(max_retries):
            # Rate limiting
            self._wait_for_rate_limit()
            
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
                    
                    elif response.status_code == 429:
                        # Rate limit hit - parse wait time and retry
                        error_text = response.text
                        print(f"Azure Claude Rate Limit (429) - Attempt {attempt + 1}/{max_retries}")
                        
                        # Try to get wait time from error message
                        wait_time = self._parse_retry_after(error_text)
                        if wait_time is None:
                            # Exponential backoff if no wait time specified
                            wait_time = base_wait_time * (2 ** attempt)
                        
                        if attempt < max_retries - 1:
                            print(f"Waiting {wait_time} seconds before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"Max retries reached. Falling back to OpenAI.")
                    
                    else:
                        print(f"Azure Claude Error: {response.status_code} - {response.text}")
                        # Fallback to OpenAI if Azure fails with other errors
                        
                except Exception as e:
                    print(f"Azure Claude Exception: {e}")
                    if attempt < max_retries - 1:
                        wait_time = base_wait_time * (2 ** attempt)
                        print(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue

        # Fallback to OpenAI after all Azure retries exhausted
        try:
            print("Using OpenAI fallback...")
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
            print(f"OpenAI Error: {e}")
            # Return empty JSON as last resort
            return '{}'

# Singleton instance
llm_client = LLMClient()
