from pymongo import MongoClient

def verify_stale():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    # Check Oreo Mocha (Code: 204703)
    data_doc = db['7-eleven_data'].find_one({'ArticleCode': {'$in': [204703, '204703']}})
    if data_doc:
        print(f"--- Oreo Mocha (7-eleven_data) ---")
        print(f"Desc: {data_doc.get('ArticleDescription')}")
        print(f"Var: {data_doc.get('7E_Variant')}")
        print(f"Flavour: {data_doc.get('7E_flavour')}")
        
        cache_doc = db['7-eleven_llm_cache'].find_one({'article_description': data_doc.get('ArticleDescription')})
        if cache_doc:
            print(f"--- Oreo Mocha (Cache) ---")
            print(f"Var: {cache_doc['result'].get('7E_Variant')}")
            print(f"Flavour: {cache_doc['result'].get('7E_flavour')}")
        else:
            print("No cache entry found for this description.")
    else:
        print("Article 204703 not found in 7-eleven_data.")

if __name__ == "__main__":
    verify_stale()
