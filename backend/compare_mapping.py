from pymongo import MongoClient

def compare_counts():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    collections = ['mapping_results', 'mapping_results_old']
    
    for coll_name in collections:
        col = db[coll_name]
        total = col.count_documents({})
        
        # Unique ArticleCodes
        unique_articles = len(col.distinct("ArticleCode"))
        
        # Unique Matched Pairs (Non-GAP)
        pipeline = [
            {'$match': {'qa_fields.match_level': {'$ne': 'GAP'}}},
            {'$group': {'_id': {'upc': '$UPC', 'item': '$ITEM'}}},
            {'$count': 'count'}
        ]
        pairs_res = list(col.aggregate(pipeline))
        pairs = pairs_res[0]['count'] if pairs_res else 0
        
        print(f"\nCollection: {coll_name}")
        print(f"  Total Documents: {total}")
        print(f"  Unique ArticleCodes: {unique_articles}")
        print(f"  Matched UPC:ITEM Pairs: {pairs}")

if __name__ == "__main__":
    compare_counts()
