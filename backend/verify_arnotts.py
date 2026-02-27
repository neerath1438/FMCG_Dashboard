import pandas as pd
from pymongo import MongoClient
import os
import sys
import json
import re

# Add backend to path to use existing LLM functions if possible, 
# but for simplicity and reliability in one-off script, I'll redefine or call the API.
# Actually, I'll just use the logic from the main mapping_analysis.py.

def normalize_text(text):
    if not text: return "NA"
    return str(text).strip().upper()

def parse_size(size_str):
    if not size_str: return 0.0
    size_str = str(size_str).upper().replace('GM', 'G')
    match = re.search(r'(\d+(\.\d+)?)', size_str)
    if match:
        return float(match.group(1))
    return 0.0

def run_arnotts_verification():
    path_711 = r'd:\git\FMCG_Dashboard\ARNOTTS_7-ELEVEN_RAW.xlsx'
    path_nielsen = r'd:\git\FMCG_Dashboard\ARNOTTS_BRAND_RAW.xlsx'
    
    df_711 = pd.read_excel(path_711)
    df_nielsen = pd.read_excel(path_nielsen)
    
    print(f"Loaded {len(df_711)} items from 7-Eleven and {len(df_nielsen)} items from Nielsen.")
    
    # 1. Level 1: Exact UPC Match
    # 7-Eleven GTIN vs Nielsen UPC
    df_711['GTIN_str'] = df_711['GTIN'].astype(str).str.strip()
    df_nielsen['UPC_str'] = df_nielsen['UPC'].astype(str).str.strip()
    
    l1_matches = []
    gaps_711 = []
    
    # Pre-process Nielsen for lookup
    nielsen_upc_map = {row['UPC_str']: row for _, row in df_nielsen.iterrows()}
    
    for _, row in df_711.iterrows():
        gtin = row['GTIN_str']
        if gtin in nielsen_upc_map:
            match = nielsen_upc_map[gtin]
            l1_matches.append({
                '7E_Article': row['ArticleDescription'],
                '7E_GTIN': gtin,
                'Nielsen_Item': match['ITEM'],
                'Nielsen_UPC': match['UPC_str'],
                'Level': 'LEVEL_1'
            })
        else:
            gaps_711.append(row)
            
    print(f"\n[SUMMARY]")
    print(f"L1 Matches Found: {len(l1_matches)}")
    print(f"Gaps (No L1 Match): {len(gaps_711)}")
    
    if l1_matches:
        print("\n--- LEVEL 1 MATCHES ---")
        for m in l1_matches:
            print(f"✅ {m['7E_Article']} ({m['7E_GTIN']}) MATCHED WITH {m['Nielsen_Item']}")
            
    if gaps_711:
        print("\n--- GAPS (POTENTIAL LEVEL 2) ---")
        # We don't have LLM data for these gaps yet in this script context.
        # But we can look for "Easy" matches based on name keywords.
        for gap in gaps_711:
            desc = gap['ArticleDescription']
            print(f"❓ GAP: {desc} (GTIN: {gap['GTIN_str']})")
            
            # Simple keyword search in Nielsen
            keywords = desc.split()[:3] # Try first 3 words
            potentials = []
            for _, n_row in df_nielsen.iterrows():
                if any(k.upper() in str(n_row['ITEM']).upper() for k in keywords):
                    potentials.append(n_row['ITEM'])
            
            if potentials:
                print(f"   Potential Matches in Nielsen: {list(set(potentials))[:3]}...")
            else:
                print(f"   No obvious keyword matches found in Nielsen.")

if __name__ == "__main__":
    run_arnotts_verification()
