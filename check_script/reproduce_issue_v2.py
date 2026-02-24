
import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add project root to path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append("d:\\FMCG_Dashboard")

# Create Mock Module
mock_db_module = MagicMock()
sys.modules["backend.database"] = mock_db_module

# Set Constants (Critical)
mock_db_module.SINGLE_STOCK_COL = "single_stock_data"
mock_db_module.MASTER_STOCK_COL = "master_stock_data"
mock_db_module.RAW_DATA_COL = "raw_data"
mock_db_module.get_collection = MagicMock()

# Setup Mock DB
mock_db = MagicMock()
mock_db_module.db = mock_db
mock_db_module.get_collection.side_effect = lambda name: mock_db[name]

# Mock Collections with explicit names matching constants
mock_single = MagicMock()
mock_master = MagicMock()
mock_cache = MagicMock()

def get_col_mock(name):
    print(f"DEBUG: Requesting collection '{name}'")
    if name == "single_stock_data": return mock_single
    if name == "master_stock_data": return mock_master
    if name == "LLM_CACHE_STORAGE": return mock_cache
    return MagicMock()

mock_db.__getitem__.side_effect = get_col_mock

# Mock Finding Docs
mock_docs = [{"ITEM": f"Item_{i}", "BRAND": "BrandX", "UPC": f"upc_{i}", "sheet_name": "wersel_match", "MARKETS": "Mkt", "MPACK": "1", "FACTS": "F"} for i in range(18)]
mock_single.find.return_value = mock_docs
mock_cache.find_one.return_value = None # Force cache miss

# Mock LLM Client (to avoid errors)
mock_llm = MagicMock()
sys.modules["backend.llm_client"] = mock_llm
mock_llm.flow2_client.chat_completion.return_value = '{"brand": "X", "flavour": "Y", "confidence": 1.0}'

# Import
from backend.processor import process_llm_mastering_flow_2

async def run_test():
    print("Running Flow 2 with Mocks v2...")
    result = await process_llm_mastering_flow_2("wersel_match")
    print(f"\nFinal Result: {result}")

if __name__ == "__main__":
    asyncio.run(run_test())
