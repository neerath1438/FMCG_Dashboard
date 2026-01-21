from pymongo import MongoClient, ASCENDING
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend directory
# Load .env from backend directory OR parent directory (for local execution)
current_dir = Path(__file__).parent
env_path = current_dir / '.env'
if not env_path.exists():
    env_path = current_dir.parent / '.env'

load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "fmcg_mastering"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Fixed Collection Names
RAW_DATA_COL = "raw_data"
SINGLE_STOCK_COL = "single_stock_data"
MASTER_STOCK_COL = "master_stock_data"

def get_collection(name):
    return db[name]

def reset_main_collections():
    """Clear all data from the 3 main collections for a fresh upload."""
    try:
        db[RAW_DATA_COL].delete_many({})
        db[SINGLE_STOCK_COL].delete_many({})
        db[MASTER_STOCK_COL].delete_many({})
        print(f"🧹 Reset complete: {RAW_DATA_COL}, {SINGLE_STOCK_COL}, {MASTER_STOCK_COL} cleared.")
    except Exception as e:
        print(f"⚠️ Reset error: {e}")

def create_indexes():
    """
    Create MongoDB indexes for faster upserts and queries.
    This dramatically speeds up the final save phase in Flow 2.
    """
    try:
        # MASTER_STOCK: Compound index on merge_id + sheet_name (for upserts)
        master_stock = db[MASTER_STOCK_COL]
        master_stock.create_index([("merge_id", ASCENDING), ("sheet_name", ASCENDING)], 
                                   name="merge_id_sheet_idx", 
                                   unique=True,
                                   background=True)
        print(f"✅ Created index: {MASTER_STOCK_COL} (merge_id + sheet_name)")
        
        # MASTER_STOCK: Index on merged_from_docs for "top merged" queries
        master_stock.create_index([("merged_from_docs", ASCENDING)], 
                                   name="merged_from_docs_idx",
                                   background=True)
        print(f"✅ Created index: {MASTER_STOCK_COL} (merged_from_docs)")
        
        # SINGLE_STOCK: Index (Fixed Collection)
        single_stock = db[SINGLE_STOCK_COL]
        single_stock.create_index([("sheet_name", ASCENDING)], 
                                   name="sheet_name_idx",
                                   background=True)
        print(f"✅ Created index: {SINGLE_STOCK_COL} (sheet_name)")
        
        # SINGLE_STOCK: Index on ITEM
        single_stock.create_index([("ITEM", ASCENDING)], 
                                   name="item_idx",
                                   background=True)
        print(f"✅ Created index: {SINGLE_STOCK_COL} (ITEM)")
        
        # RAW collection: Index on sheet_name
        raw_coll = db[RAW_DATA_COL]
        raw_coll.create_index([("sheet_name", ASCENDING)], 
                               name="sheet_name_idx",
                               background=True)
        print(f"✅ Created index: {RAW_DATA_COL} (sheet_name)")
        
        print("🚀 All MongoDB indexes created successfully!")
        
    except Exception as e:
        print(f"⚠️ Index creation error (might already exist): {e}")

# Export db for direct access when needed (e.g., reset endpoint)
__all__ = ['get_collection', 'db', 'create_indexes', 'reset_main_collections', 'RAW_DATA_COL', 'SINGLE_STOCK_COL', 'MASTER_STOCK_COL']
