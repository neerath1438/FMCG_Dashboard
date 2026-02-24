import asyncio
import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from backend.processor import process_llm_mastering_flow_2

async def main():
    print("🚀 Starting Flow 2 Mastering...")
    # Use 'wersel_match' as it's the fixed sheet name in processor.py
    result = await process_llm_mastering_flow_2("wersel_match")
    print("\n✅ Mastering Complete!")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
