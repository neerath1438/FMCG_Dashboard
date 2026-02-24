from pymongo import MongoClient

def check_apollo():
    client = MongoClient("mongodb://localhost:27017")
    db = client["fmcg_mastering"]
    coll = db["raw_data"]
    
    upc = 726165011049
    mat_col = "MAT Nov'24"
    
    print(f"Checking Raw Records for UPC: {upc}")
    records = list(coll.find({"UPC": upc}))
    
    if not records:
        print("No records found for numeric UPC. Checking string UPC...")
        records = list(coll.find({"UPC": str(upc)}))

    if not records:
        print("No records found at all.")
        return

    for r in records:
        item = r.get("ITEM")
        brand = r.get("BRAND")
        mat = r.get(mat_col, 0)
        print(f"ITEM: {item} | BRAND: {brand} | MAT: {mat}")

    # Find the leader
    leader = max(records, key=lambda x: float(x.get(mat_col, 0)) if x.get(mat_col) else 0)
    print("\n--- GOLLING LEADER ---")
    print(f"LEADER ITEM: {leader.get('ITEM')}")
    print(f"LEADER BRAND: {leader.get('BRAND')}")
    print(f"LEADER MAT: {leader.get(mat_col)}")

    client.close()

if __name__ == "__main__":
    check_apollo()
