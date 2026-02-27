from pymongo import MongoClient

db = MongoClient('mongodb://localhost:27017')['fmcg_mastering']
items = [
    "Julie's Cocoro Chocolate Wafer Rolls 100g",
    "Julie's One Bite's Chocolate 85g",
    "Julie's One Bite's Peanut Butter 73g",
    "Julie's Butter Crackers 135g"
]
for item in items:
    d = db['7-eleven_data'].find_one({'ArticleDescription': item})
    if d:
        print(f"Desc: {d.get('ArticleDescription')}")
        print(f"  Var: {d.get('7E_Variant')} | Flav: {d.get('7E_flavour')} | Size: {d.get('7E_Nrmsize')}")
    else:
        print(f"Not found: {item}")
