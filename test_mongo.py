from pymongo import MongoClient
import sys

try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    print("Testing connection...")
    print(f"Databases: {client.list_database_names()}")
    print("Connection SUCCESSFUL")
except Exception as e:
    print(f"Connection FAILED: {e}")
    sys.exit(1)
