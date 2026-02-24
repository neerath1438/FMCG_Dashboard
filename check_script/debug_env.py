
import os
from dotenv import load_dotenv

env_path = "d:/FMCG_Dashboard/.env"

if os.path.exists(env_path):
    load_dotenv(env_path)
    print("--- Detailed LLM Configuration ---")
    vars_to_check = [
        "AZURE_CLAUDE_ENDPOINT",
        "AZURE_CLAUDE_API_KEY",
        "AZURE_CLAUDE_MODEL_NAME",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT"
    ]
    for v in vars_to_check:
        val = os.getenv(v)
        if val:
            if "KEY" in v or "ENDPOINT" in v:
                print(f"{v}: [CONFIGURED]")
            else:
                print(f"{v}: {val}")
        else:
            print(f"{v}: [NOT SET]")
else:
    print(f"Error: {env_path} not found.")
