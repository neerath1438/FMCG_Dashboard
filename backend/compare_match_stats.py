from pymongo import MongoClient

def compare_stats():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    colls = ['mapping_results', 'mapping_results_new']
    
    for c_name in colls:
        col = db[c_name]
        total = col.count_documents({})
        l1 = col.count_documents({'qa_fields.match_level': 'LEVEL_1'})
        l2 = col.count_documents({'qa_fields.match_level': 'LEVEL_2'})
        gap = col.count_documents({'qa_fields.match_level': 'GAP'})
        
        print(f"\nCollection: {c_name}")
        print(f"  Total: {total}")
        print(f"  Level 1 (Exact UPC): {l1}")
        print(f"  Level 2 (Attribute): {l2}")
        print(f"  GAP: {gap}")
        print(f"  Match Rate: {round((l1+l2)/total*100, 2)}%")

if __name__ == "__main__":
    compare_stats()
