from pymongo import MongoClient

def find_lost_articles():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    # Get ArticleCodes from Mapping Results (Non-GAP)
    current_articles = set(db['mapping_results'].distinct("ArticleCode", {"qa_fields.match_level": {"$ne": "GAP"}}))
    old_articles = set(db['mapping_results_old'].distinct("ArticleCode", {"qa_fields.match_level": {"$ne": "GAP"}}))
    
    lost = old_articles - current_articles
    gained = current_articles - old_articles
    
    print(f"Lost ArticleCodes: {len(lost)}")
    for a in list(lost)[:10]:
        print(f"  - {a}")
        
    print(f"\nGained ArticleCodes: {len(gained)}")
    for a in list(gained)[:10]:
        print(f"  - {a}")
        
    # Pick one lost article and check its data in 7-eleven_data vs cache
    if lost:
        sample = list(lost)[0]
        print(f"\n--- Analysis for Sample Lost Article: {sample} ---")
        doc = db['7-eleven_data'].find_one({"ArticleCode": sample})
        if doc:
            print(f"Current 7-Eleven Entry: {doc.get('ArticleDescription_clean')} | {doc.get('7E_Nrmsize')} | {doc.get('7E_Variant')}")
            # Check why it might not match (Simplified check)
            # Find a potential match in master_stock_data
            brand = doc.get("Brand", "")
            matches = list(db['master_stock_data'].find({"BRAND": brand}).limit(3))
            print(f"Potential Nielsen Matches for Brand '{brand}':")
            for m in matches:
                print(f"  - {m.get('ITEM')} | {m.get('size')}")

if __name__ == "__main__":
    find_lost_articles()
