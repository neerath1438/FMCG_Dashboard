import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

load_dotenv('backend/.env')

from backend.processor import process_llm_mastering_flow_2

async def run_flow2():
    print("Starting Flow 2 Re-processing...")
    # Using 'wersel_match' as the sheet name as seen in the user's JSON
    sheet_name = "wersel_match"
    try:
        results = await process_llm_mastering_flow_2(sheet_name)
        print(f"Flow 2 complete: {results}")
    except Exception as e:
        print(f"Error during Flow 2: {e}")

if __name__ == "__main__":
    asyncio.run(run_flow2())
