import json
import sys
import argparse
from pymongo import MongoClient

# Database Config
DB_NAME = "fmcg_mastering"
COLLECTION_NAME = "LLM_CACHE_STORAGE"
DEFAULT_URI = "mongodb://localhost:27017"
DOCKER_URI = "mongodb://localhost:27017"  # Since ports are mapped, localhost works outside docker too

def export_cache(uri, file_path):
    print(f"🔗 Connecting to {uri}...")
    client = MongoClient(uri)
    db = client[DB_NAME]
    coll = db[COLLECTION_NAME]
    
    print(f"🔍 Fetching documents from {COLLECTION_NAME}...")
    docs = list(coll.find({}, {"_id": 0}))
    
    print(f"💾 Saving {len(docs)} documents to {file_path}...")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    
    print("✅ Export complete!")

def import_cache(uri, file_path):
    print(f"🔗 Connecting to {uri}...")
    client = MongoClient(uri)
    db = client[DB_NAME]
    coll = db[COLLECTION_NAME]
    
    print(f"📖 Reading data from {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            docs = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found!")
        return

    print(f"📥 Upserting {len(docs)} documents into {COLLECTION_NAME}...")
    count = 0
    for doc in docs:
        # Upsert based on the 'item' field
        coll.update_one(
            {"item": doc["item"]},
            {"$set": doc},
            upsert=True
        )
        count += 1
        if count % 100 == 0:
            print(f"   Progress: {count}/{len(docs)}")
            
    print(f"✅ Import complete! Total processed: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate LLM Cache between MongoDB instances.")
    parser.add_argument("--mode", choices=["export", "import"], required=True, help="Mode: export (local) or import (server)")
    parser.add_argument("--file", default="llm_cache_dump.json", help="JSON file path for dump")
    parser.add_argument("--uri", default=DEFAULT_URI, help="MongoDB URI")
    
    args = parser.parse_args()
    
    if args.mode == "export":
        export_cache(args.uri, args.file)
    else:
        import_cache(args.uri, args.file)
