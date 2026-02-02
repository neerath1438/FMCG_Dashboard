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

if env_path.exists():
    load_dotenv(env_path)

class LLMClient:
    def __init__(self):
        # Primary: Azure Claude
        self.use_azure = True
        self.azure_endpoint = os.getenv("AZURE_CLAUDE_ENDPOINT")
        self.azure_key = os.getenv("AZURE_CLAUDE_API_KEY")
        self.azure_model = os.getenv("AZURE_CLAUDE_MODEL_NAME", "claude-sonnet-4-5")

        # Fallback: Azure OpenAI (CEO requirement - use Azure, not direct OpenAI)
        try:
            from openai import AzureOpenAI
            self.azure_openai_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),  # SDK expects AZURE_OPENAI_API_KEY
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )

            self.azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
            self.has_azure_openai = True
        except Exception as e:
            print(f"Azure OpenAI not configured: {e}")
            self.has_azure_openai = False
        
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

                    response = requests.post(self.azure_endpoint, headers=headers, json=payload, timeout=300)
                    
                    if response.status_code == 200:
                        res_json = response.json()
                        return res_json['content'][0]['text']
                    
                    elif response.status_code == 429:
                        print(f"Azure Claude Rate Limit (429) - Switching to Azure OpenAI fallback...")
                        break 
                    
                    else:
                        print(f"Azure Claude Error: {response.status_code} - {response.text}")
                        break
                        
                except Exception as e:
                    print(f"Azure Claude Exception: {e}")
                    if attempt < max_retries - 1:
                        wait_time = base_wait_time * (2 ** attempt)
                        print(f"Retrying Claude in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        break

        # Fallback to Azure OpenAI after all Azure Claude retries exhausted or 429
        if self.has_azure_openai:
            print("Using Azure OpenAI fallback...")
            # Reuse logic from OpenAIOnlyClient for the fallback
            fb_retries = 5
            fb_base_delay = 2
            for fb_attempt in range(fb_retries):
                try:
                    resp = self.azure_openai_client.chat.completions.create(
                        model=self.azure_openai_deployment,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    print("Azure OpenAI fallback successful")
                    return resp.choices[0].message.content
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RateLimitReached" in error_msg:
                        retry_after = self._parse_retry_after(error_msg)
                        if retry_after:
                            delay = retry_after + 1.5
                        else:
                            import random
                            delay = (fb_base_delay * (2 ** fb_attempt)) * random.uniform(0.5, 1.5)
                        
                        print(f"Fallback Rate Limit (429). Waiting {delay:.2f}s (Attempt {fb_attempt+1}/{fb_retries})")
                        delay = min(delay, 60) # ✅ Cap delay to 60s
                        time.sleep(delay)
                        continue
                    
                    print(f"❌ Azure OpenAI Fallback Error: {e}")
                    break
        else:
            print("Azure OpenAI not configured - no fallback available")
        
        return '{}'


class OpenAIOnlyClient:
    """
    OpenAI-only client for Flow 2 processing.
    Faster and more reliable than Claude for bulk processing.
    """
    def __init__(self):
        try:
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
            print("OpenAI-only client initialized for Flow 2")
        except Exception as e:
            print(f"OpenAI client initialization failed: {e}")
            self.client = None
    
    def _parse_retry_after(self, error_text):
        """Extract wait time from rate limit error message"""
        try:
            # Look for "retry after X seconds" or "wait X seconds" patterns
            match = re.search(r'retry after (\d+) second', error_text, re.IGNORECASE)
            if not match:
                match = re.search(r'wait (\d+) second', error_text, re.IGNORECASE)
            
            if match:
                return int(match.group(1))
        except:
            pass
        return None

    def chat_completion(self, system_prompt, user_message, temperature=0, max_tokens=1000):
        if not self.client:
            return '{}'
        
        max_retries = 10  # Increased for stability in large runs
        base_delay = 2   # Slightly higher base delay
        
        for attempt in range(max_retries):
            try:
                resp = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return resp.choices[0].message.content
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RateLimitReached" in error_msg:
                    # ✅ SMART RETRY: Follow Azure's recommended wait time
                    retry_after = self._parse_retry_after(error_msg)
                    if retry_after:
                        delay = retry_after + 1.5  # Add small buffer to be 100% safe
                    else:
                        import random
                        jitter = random.uniform(0.5, 1.5)
                        delay = (base_delay * (2 ** attempt)) * jitter
                    
                    print(f"Rate limit hit (429) for '{user_message[:30]}...'. Requested wait: {retry_after if retry_after else 'N/A'}s. Waiting {delay:.2f}s (Attempt {attempt+1}/{max_retries})")
                    delay = min(delay, 60) # Cap delay at 60s
                    time.sleep(delay)
                    continue
                
                print(f"OpenAI Error: {e}")
                return '{}'
        
        print(f"Failed after {max_retries} attempts due to rate limits.")
        return '{}'


# Singleton instances
llm_client = LLMClient()  # For chatbot (uses Claude + fallback)
flow2_client = OpenAIOnlyClient()  # For Flow 2 (OpenAI only)
