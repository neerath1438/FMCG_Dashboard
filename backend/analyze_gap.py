from pymongo import MongoClient

def analyze_lost_pair():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    
    # Find a UPC that matched in OLD but is GAP in NEW
    old_matches = db['mapping_results_old'].find({'qa_fields.match_level': {'$ne': 'GAP'}})
    
    match_count = 0
    for old in old_matches:
        new = db['mapping_results'].find_one({'UPC': old['UPC'], 'ITEM': old['ITEM']})
        if new and new['qa_fields']['match_level'] == 'GAP':
            print(f"\n[!] LOST MATCH FOUND for UPC: {old['UPC']} | ITEM: {old['ITEM']}")
            print(f"  Nielsen: Brand={old.get('Brand')}, Variant={old.get('VARIANT')}, Size={old.get('size') or old.get('original_size')}")
            
            # Check CURRENT 7E Data for the old matched ArticleCode
            code = old.get('ArticleCode')
            if code:
                curr_7e = db['7-eleven_data'].find_one({'ArticleCode': {'$in': [code, str(code), int(code) if str(code).isdigit() else code]}})
                if curr_7e:
                    print(f"  7-Eleven: Clean_Desc={curr_7e.get('ArticleDescription_clean')}")
                    print(f"  7-Eleven: Brand={curr_7e.get('L4_Description_Brand')}, Variant={curr_7e.get('7E_Variant')}, Flavour={curr_7e.get('7E_flavour')}, Size={curr_7e.get('7E_Nrmsize')}")
            
            match_count += 1
            if match_count >= 5:
                break

if __name__ == "__main__":
    analyze_lost_pair()
