from pymongo import MongoClient

def calculate_coverage():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    col = db['mapping_results']
    
    # 1. Total unique (Main_UPC, Matched_ITEM) pairs matched (Non-GAP)
    pipeline_pairs = [
        {'$match': {'Match_Level': {'$ne': 'GAP'}}},
        {'$group': {'_id': {'upc': '$Main_UPC', 'item': '$Matched_ITEM'}}},
        {'$count': 'count'}
    ]
    pairs_res = list(col.aggregate(pipeline_pairs))
    current_pairs = pairs_res[0]['count'] if pairs_res else 0
    
    # 2. Total unique ArticleCodes matched (Non-GAP)
    pipeline_articles = [
        {'$match': {'Match_Level': {'$ne': 'GAP'}, 'ArticleCode': {'$ne': None}}},
        {'$group': {'_id': '$ArticleCode'}},
        {'$count': 'count'}
    ]
    articles_res = list(col.aggregate(pipeline_articles))
    current_articles = articles_res[0]['count'] if articles_res else 0
    
    # Benchmark targets from user
    target_articles = 649
    target_pairs = 1118
    
    # Calculate rates
    article_coverage = (current_articles / target_articles * 100) if target_articles else 0
    pair_coverage = (current_pairs / target_pairs * 100) if target_pairs else 0
    
    print("\n--- Final Mapping Coverage Metrics (7-Eleven Centric) ---")
    print(f"1. ArticleCode Coverage:")
    print(f"   Benchmark Target: {target_articles}")
    print(f"   Identified Now:   {current_articles}")
    print(f"   Missing:          {target_articles - current_articles}")
    print(f"   Coverage Rate:    {round(article_coverage, 2)}%")
    
    print(f"\n2. UPC:ITEM Pair Coverage (Nielsen Side):")
    print(f"   Benchmark Target: {target_pairs}")
    print(f"   Identified Now:   {current_pairs}")
    print(f"   Missing:          {target_pairs - current_pairs}")
    print(f"   Overall Match Rate: {round(pair_coverage, 2)}%")
    
    # Derived Metrics (Approximated)
    precision = 96.17 # User's benchmark precision
    recall = pair_coverage
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0
    
    print(f"\n3. Evaluation Perspective (Approx):")
    print(f"   Precision: {precision}%")
    print(f"   Recall (Current): {round(recall, 2)}%")
    print(f"   F1 Score: {round(f1/100, 2)}")

if __name__ == "__main__":
    calculate_coverage()
