from backend.database import get_collection, MASTER_STOCK_COL
import json

def write_sample():
    master = get_collection(MASTER_STOCK_COL)
    docs = list(master.find().limit(50))
    with open("master_sample.json", "w") as f:
        json.dump(docs, f, indent=2, default=str)
    print("Sample written to master_sample.json")

if __name__ == "__main__":
    write_sample()
