from pymongo import MongoClient
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

# Export db for direct access when needed (e.g., reset endpoint)
__all__ = ['get_collection', 'db']
