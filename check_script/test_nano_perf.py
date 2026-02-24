
import os
import sys
import json
import time
from openai import AzureOpenAI

# Test Credentials - loaded from environment variables (set in .env)
ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-nano")
API_VERSION = "2025-01-01-preview"

client = AzureOpenAI(
    api_key=API_KEY,
    api_version=API_VERSION,
    azure_endpoint=ENDPOINT
)

# Test items
test_items = [
    "GLICO BRAND POCKY CHOCO BANANA FLAVOUR 25GM",
    "GLICO BRAND POCKY MILK FLAVOUR 25GM",
    "GLICO CHOCO BANANA 25GM",
    "OREO VNL 133G",
    "MEIJI YAN YAN CHOCO 50G",
    "KINDER HAPPY HIPPO 20.7G"
]

# System Prompt (Copied from processor.py)
system_prompt = """
You are an FMCG product mastering expert specializing in the Malaysian market.
Your task is to extract standardized attributes from raw product descriptions.
Return JSON only:
{
  "brand": "Standardized Brand Name",
  "product_line": "Specific Sub-Brand or Line (e.g., YAN YAN, HELLO PANDA, POCKY)",
  "flavour": "Standardized Flavour Name",
  "product_form": "Standardized Form (e.g., STICK, WAFER, BISCUIT)",
  "is_sugar_free": boolean,
  "size": "Standardized Size",
  "base_item": "Standardized Full Generic Name (Include weight)",
  "confidence": 0.0 to 1.0
}
"""

def test_model(item):
    print(f"\nProcessing: '{item}'")
    try:
        start_time = time.time()
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f'ITEM DESCRIPTION: "{item}"'}
            ]
        )
        duration = time.time() - start_time
        content = response.choices[0].message.content.strip()
        print(f"Time taken: {duration:.2f}s")
        print(f"Response: {content}")
        return json.loads(content)
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        # print(traceback.format_exc())
        return None

results = []
for item in test_items:
    res = test_model(item)
    if res:
        results.append({"input": item, "output": res})

# Evaluation summary
print("\n--- TEST EVALUATION SUMMARY ---")
for r in results:
    inp = r["input"]
    out = r["output"]
    
    issues = []
    if "POCKY" in inp and out.get("product_line") != "POCKY":
        issues.append("Missing POCKY product line")
    if "YAN YAN" in inp and out.get("product_line") != "YAN YAN":
        issues.append("Missing YAN YAN product line")
    if not out.get("brand") or not out.get("flavour"):
        issues.append("Missing key attributes")
    
    status = "✅ PASS" if not issues else f"❌ FAIL ({', '.join(issues)})"
    print(f"{inp} -> {status}")
