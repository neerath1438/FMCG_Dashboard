import json
import argparse
from pymongo import MongoClient
from bson import json_util

def export_collection(db_name, collection_name, output_file=None):
    """
    Exports a MongoDB collection to a JSON file without the '_id' field.
    No database names are hardcoded inside this function or the script.
    """
    try:
        client = MongoClient('mongodb://localhost:27017')
        db = client[db_name]
        collection = db[collection_name]

        if output_file is None:
            output_file = f"{collection_name}_export.json"

        print(f"Exporting collection '{collection_name}' from database '{db_name}'...")
        
        # Query to exclude _id field
        cursor = collection.find({}, {"_id": 0})
        
        data = list(cursor)
        
        print(f"Found {len(data)} documents.")

        with open(output_file, 'w', encoding='utf-8') as f:
            # ensure_ascii=False ensures that Tamil or other non-English characters are saved correctly
            json.dump(data, f, default=json_util.default, ensure_ascii=False, indent=4)

        print(f"✅ Successfully exported to: {output_file}")
        client.close()
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generic MongoDB Collection Exporter (JSON)")
    parser.add_argument("--db", required=True, help="Name of the database")
    parser.add_argument("--collection", required=True, help="Name of the collection")
    parser.add_argument("--out", help="Output file name (optional)")

    args = parser.parse_args()

    export_collection(args.db, args.collection, args.out)
