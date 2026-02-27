from pymongo import MongoClient
import re

client = MongoClient('mongodb://localhost:27017/')
db = client['fmcg_mastering']
coll_master = db['master_stock_data']
coll_results = db['mapping_results']

# Get Market Heroes (items not matched in the current run)
market_heroes = list(coll_results.find({"Match_Level": "MARKET_HERO", "Source": "Master Stock (Market Gap)"}))

# 11 GAP items to check
gaps_7e = [
    {"desc": "Oreo Ice Cream Blueberry 29.4g", "gtin": "7622300442477", "flavour": "BLUEBERRY", "size": 29.4},
    {"desc": "Oreo Golden 133g", "gtin": "7622300484071", "flavour": "VANILLA", "size": 133},
    {"desc": "Oreo Ice Cream Orange 29.4g", "gtin": "7622300442231", "flavour": "ORANGE", "size": 29.4},
    {"desc": "Oreo Strawberry Creme 137g - LTO", "gtin": "2000001112755", "flavour": "STRAWBERRY", "size": 137},
    {"desc": "Oreo Phone Ring (Contest Premium)", "gtin": "9566771044991", "flavour": "NONE", "size": 0},
    {"desc": "Oreo Spiderman Keychain FOC", "gtin": "5060373572387", "flavour": "NONE", "size": 0},
    {"desc": "Mooncake Chocolate Lava Oreo 180g", "gtin": "9555234400757", "flavour": "CHOCOLATE", "size": 180},
    {"desc": "Oreo Mini Box Mocha 40.8g", "gtin": "7622210541925", "flavour": "MOCHA", "size": 40.8},
    {"desc": "Oreo Mint Sandwich Biscuits 154g", "gtin": "7622210626028", "flavour": "MINT", "size": 154},
    {"desc": "OREO STRAWBERRY CHEESECAKE BISCUITS 154G", "gtin": "7622210635105", "flavour": "STRAWBERRY CHEESECAKE", "size": 154},
    {"desc": "Oreo Lychee Orange 119.6g - LTD", "gtin": "7622201729967", "flavour": "LYCHEE ORANGE", "size": 119.6}
]

print(f"{'7-Eleven GAP Item':<40} | {'Potential Market Match':<40} | {'Status'}")
print("-" * 110)

def normalize(text):
    return str(text).upper().replace(" ", "").replace("-", "").replace(".", "")

for gap in gaps_7e:
    found_match = "GENUINE GAP"
    match_desc = "-"
    
    # Try to find a match in Market Heroes
    for hero in market_heroes:
        h_item = hero.get("Matched_ITEM") or ""
        h_brand = hero.get("7E_Brand") or ""
        h_size_str = str(hero.get("7E_Size") or "0")
        
        # Parse size from hero
        try:
            h_size = float(re.findall(r"[\d\.]+", h_size_str)[0])
        except:
            h_size = 0.0
            
        # 1. Brand Match (OREO)
        if "OREO" not in normalize(h_brand) and "OREO" not in normalize(h_item):
            continue
            
        # 2. Check Keywords
        desc_norm = normalize(gap['desc'])
        hero_norm = normalize(h_item)
        
        # Check specific flavor/keyword overlap
        flav = normalize(gap['flavour'])
        
        # Level 2 Logic check
        size_diff = abs(gap['size'] - h_size)
        
        if flav != "NONE" and flav in hero_norm and size_diff <= 10.0:
            # Check for bidirectional safety (e.g. THINS, MINI, ICE CREAM)
            safety_words = ["THINS", "MINI", "ICE CREAM", "GOLDEN", "MOONCAKE", "WAFER"]
            safe = True
            for sw in safety_words:
                sw_n = normalize(sw)
                if (sw_n in desc_norm) != (sw_n in hero_norm):
                    safe = False
                    break
            
            if safe:
                found_match = "POTENTIAL LEVEL_2"
                match_desc = h_item
                break

    print(f"{gap['desc'][:40]:<40} | {match_desc[:40]:<40} | {found_match}")

print("\n--- Detailed Master Stock Search for Gaps ---")
for gap in gaps_7e:
    if gap['size'] > 0:
        words = [w for w in gap['desc'].upper().split() if len(w) > 3 and w not in ["OREO", "BISCUITS", "CREME"]]
        query = {"BRAND": "OREO"}
        if words:
            query["ITEM"] = {"$regex": "|".join(words), "$options": "i"}
        
        results = list(coll_master.find(query))
        if results:
            print(f"\nGap: {gap['desc']}")
            for r in results:
                print(f"  -> Master: {r.get('ITEM')} ({r.get('NRMSIZE')}g)")
