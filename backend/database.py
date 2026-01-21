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

def get_collection(name):
    return db[name]

def create_indexes():
    """
    Create MongoDB indexes for faster upserts and queries.
    This dramatically speeds up the final save phase in Flow 2.
    """
    try:
        # MASTER_STOCK: Compound index on merge_id + sheet_name (for upserts)
        master_stock = db["MASTER_STOCK"]
        master_stock.create_index([("merge_id", ASCENDING), ("sheet_name", ASCENDING)], 
                                   name="merge_id_sheet_idx", 
                                   unique=True,
                                   background=True)
        print("✅ Created index: MASTER_STOCK (merge_id + sheet_name)")
        
        # MASTER_STOCK: Index on merged_from_docs for "top merged" queries
        master_stock.create_index([("merged_from_docs", ASCENDING)], 
                                   name="merged_from_docs_idx",
                                   background=True)
        print("✅ Created index: MASTER_STOCK (merged_from_docs)")
        
        # SINGLE_STOCK: Index on sheet_name for faster queries
        single_stock = db["SINGLE_STOCK"]
        single_stock.create_index([("sheet_name", ASCENDING)], 
                                   name="sheet_name_idx",
                                   background=True)
        print("✅ Created index: SINGLE_STOCK (sheet_name)")
        
        # SINGLE_STOCK: Index on ITEM for faster lookups
        single_stock.create_index([("ITEM", ASCENDING)], 
                                   name="item_idx",
                                   background=True)
        print("✅ Created index: SINGLE_STOCK (ITEM)")
        
        # RAW collections: Index on sheet_name
        for sheet in ["Sheet1_RAW", "Nielsen_Wersel_Test_RAW"]:
            try:
                raw_coll = db[sheet]
                raw_coll.create_index([("sheet_name", ASCENDING)], 
                                       name="sheet_name_idx",
                                       background=True)
                print(f"✅ Created index: {sheet} (sheet_name)")
            except:
                pass  # Collection might not exist yet
        
        print("🚀 All MongoDB indexes created successfully!")
        
    except Exception as e:
        print(f"⚠️ Index creation error (might already exist): {e}")

# Export db for direct access when needed (e.g., reset endpoint)
__all__ = ['get_collection', 'db', 'create_indexes']
