from pymongo import MongoClient
import codecs

client = MongoClient('mongodb://localhost:27017')
db = client['fmcg_mastering']
coll = db['master_stock_data']

# Check specific items that look like duplicates
duplicate_candidates = ["HATARI CHOCOLATE CREAM 200GM", "GLICO POCKY 45GM X1 STRAWBERRY"]

with codecs.open('duplicate_explanation.txt', 'w', 'utf-8') as f:
    f.write("DUPLICATE ANALYSIS REPORT\n")
    f.write("=" * 60 + "\n\n")

    for item_name in duplicate_candidates:
        f.write(f"ITEM: {item_name}\n")
        f.write("-" * 30 + "\n")
        
        docs = list(coll.find({"ITEM": item_name}).limit(10))
        
        for d in docs:
            # We need to find where Market/Facts are stored. 
            # In master_stock_data, they are usually in the top level after merge.
            market = d.get("MARKET") or d.get("MARKETS") or "N/A"
            facts = d.get("FACT") or d.get("FACTS") or "N/A"
            pack = d.get("PACK") or d.get("MPACK") or "N/A"
            
            f.write(f"-> Master ID: {d.get('merge_id')}\n")
            f.write(f"   Market: {market} | Pack: {pack} | Fact: {facts}\n")
            f.write(f"   Merge Items Count: {len(d.get('merge_items', []))}\n\n")
        
        f.write("\n")

print("Duplicate explanation report generated: duplicate_explanation.txt")
