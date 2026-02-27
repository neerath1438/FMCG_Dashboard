import os
import re
from pymongo import MongoClient

def levenshtein_similarity(s1, s2):
    if s1 == s2: return 1.0
    if not s1 or not s2: return 0.0
    rows = len(s1) + 1
    cols = len(s2) + 1
    dist = [[0 for _ in range(cols)] for _ in range(rows)]
    for i in range(1, rows): dist[i][0] = i
    for i in range(1, cols): dist[0][i] = i
    for col in range(1, cols):
        for row in range(1, rows):
            cost = 0 if s1[row-1] == s2[col-1] else 1
            dist[row][col] = min(dist[row-1][col] + 1, dist[row][col-1] + 1, dist[row-1][col-1] + cost)
    max_len = max(len(s1), len(s2))
    return 1.0 - (dist[rows-1][cols-1] / max_len)

def check_scores():
    client = MongoClient('mongodb://localhost:27017')
    db = client['fmcg_mastering']
    coll_master = db['master_stock_data']
    
    unique_b_n = list(set([str(m.get("BRAND", "")).upper() for m in coll_master.find()]))
    
    missing_brands = [
        "HUNTLEY & PALMERS",
        "NESTLE KIT KAT",
        "FERRERO ROCHER",
        "JULIES OAT 25",
        "MCVITIES DIGESTIVE"
    ]
    
    for mb in missing_brands:
        print(f"\nAnalyzing Brand: {mb}")
        scores = []
        for bn in unique_b_n:
            score = levenshtein_similarity(mb, bn)
            if score > 0.6:
                scores.append((bn, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        for s in scores[:5]:
            print(f"  Match: {s[0]}, Score: {round(s[1], 3)}")

if __name__ == "__main__":
    check_scores()
