from pymongo import MongoClient

def compare():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    gold_matches = { (d['UPC'], d['ITEM']): d for d in db['mapping_results_new'].find({'qa_fields.match_level': {'$ne': 'GAP'}}) }
    curr_matches = { (d['UPC'], d['ITEM']): d for d in db['mapping_results'].find({'qa_fields.match_level': {'$ne': 'GAP'}}) }
    
    only_gold = set(gold_matches.keys()) - set(curr_matches.keys())
    only_curr = set(curr_matches.keys()) - set(gold_matches.keys())
    
    print(f"Only in Gold (1018): {len(only_gold)}")
    print(f"Only in Current (971): {len(only_curr)}")
    
    if only_gold:
        print("\n--- Examples only in Gold ---")
        for i, key in enumerate(list(only_gold)[:3]):
            doc = gold_matches[key]
            print(f"Item: {key[1]} | UPC: {key[0]}")
            print(f"  7E Article: {doc.get('Article_Description')}")
            print(f"  Match Level: {doc['qa_fields'].get('match_level')}")
            print(f"  Match Type: {doc['qa_fields'].get('match_type')}")

if __name__ == "__main__":
    compare()
