from pymongo import MongoClient

def calculate_final():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    col = db['mapping_results']
    
    # Get all matched documents
    matched = list(col.find({'qa_fields.match_level': {'$ne': 'GAP'}}))
    
    # 1. Unique (UPC, ITEM) pairs
    pairs = set()
    for d in matched:
        pairs.add((d.get('UPC'), d.get('ITEM')))
    
    # 2. Unique ArticleCodes
    articles = set()
    for d in matched:
        # Check both cases just in case
        code = d.get('ArticleCode') or d.get('article_code')
        if code:
            articles.add(str(code))
            
    print(f"DEBUG: Matched count from find: {len(matched)}")
    print(f"RESULT_PAIRS: {len(pairs)}")
    print(f"RESULT_ARTICLES: {len(articles)}")

if __name__ == "__main__":
    calculate_final()
