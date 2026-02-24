import json
import argparse
from pymongo import MongoClient
from bson import json_util

def import_collection(db_name, collection_name, input_file):
    """
    Imports a JSON file into a MongoDB collection.
    No database names or collection names are hardcoded.
    """
    try:
        client = MongoClient('mongodb://localhost:27017')
        db = client[db_name]
        collection = db[collection_name]

        print(f"Reading data from '{input_file}'...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f, object_hook=json_util.object_hook)

        if not isinstance(data, list):
            # If the JSON is a single object, wrap it in a list
            data = [data]

        print(f"Importing {len(data)} documents into '{db_name}.{collection_name}'...")
        
        if len(data) > 0:
            result = collection.insert_many(data)
            print(f"✅ Successfully imported {len(result.inserted_ids)} documents.")
        else:
            print("⚠️ No data found in the file to import.")

        client.close()
    except Exception as e:
        print(f"❌ Error during import: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generic MongoDB Collection Importer (JSON)")
    parser.add_argument("--db", required=True, help="Name of the target database")
    parser.add_argument("--collection", required=True, help="Name of the target collection")
    parser.add_argument("--file", required=True, help="Path to the JSON file to import")

    args = parser.parse_args()

    import_collection(args.db, args.collection, args.file)
