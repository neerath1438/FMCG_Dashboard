import pandas as pd
import re

def normalize_text(text):
    if not text: return ""
    return str(text).strip().upper()

def parse_size(size_str):
    if not size_str: return 0.0
    size_str = str(size_str).upper().replace('GM', 'G').replace('GME', 'G')
    match = re.search(r'(\d+(\.\d+)?)', size_str)
    if match:
        return float(match.group(1))
    return 0.0

def get_keywords(text):
    text = re.sub(r'[^A-Z0-9\s]', ' ', normalize_text(text))
    words = text.split()
    ignore = ['ARNOTTS', 'ARNOTT', 'S', 'BRAND', 'BISCUITS', 'CRACKER', 'ORIGINAL', 'RICE', 'CRISPY']
    return [w for w in words if w not in ignore and len(w) > 2]

def run_arnotts_qa():
    path_711 = r'd:\git\FMCG_Dashboard\ARNOTTS_7-ELEVEN_RAW.xlsx'
    path_nielsen = r'd:\git\FMCG_Dashboard\ARNOTTS_BRAND_RAW.xlsx'
    
    df_711 = pd.read_excel(path_711)
    df_nielsen = pd.read_excel(path_nielsen)
    
    df_nielsen['UPC_str'] = df_nielsen['UPC'].astype(str).str.strip()
    df_nielsen['size_val'] = df_nielsen['NRMSIZE'].apply(parse_size)
    nielsen_upc_map = {row['UPC_str']: row for _, row in df_nielsen.iterrows()}
    
    results = []
    
    for _, row in df_711.iterrows():
        gtin = str(row['GTIN']).strip()
        desc = row['ArticleDescription']
        size_7e = parse_size(desc)
        keywords_7e = get_keywords(desc)
        
        match_info = {
            'Article_Description': desc,
            'GTIN': gtin,
            'Matched_Item': "GAP",
            'Level': "GAP",
            'Match_Score': 0,
            'Note': "Not Found in Nielsen (Needs Master Update)"
        }
        
        # Level 1: Exact UPC
        if gtin in nielsen_upc_map:
            n_row = nielsen_upc_map[gtin]
            match_info.update({
                'Matched_Item': n_row['ITEM'],
                'Level': "LEVEL_1",
                'Note': "Perfect Match! ✅"
            })
        else:
            # Level 2: Attribute Search
            candidates = []
            for _, n_row in df_nielsen.iterrows():
                k_nielsen = get_keywords(n_row['ITEM'])
                common = set(keywords_7e) & set(k_nielsen)
                score = len(common)
                size_diff = abs(n_row['size_val'] - size_7e)
                
                if score >= 1 and size_diff <= 20.0:
                    candidates.append((score, size_diff, n_row))

            if candidates:
                # Get max score
                max_score = max(c[0] for c in candidates)
                top_candidates = [c for c in candidates if c[0] == max_score]
                
                # Pick best by size diff
                top_candidates.sort(key=lambda x: x[1])
                best_cand_tuple = top_candidates[0]
                best_cand = best_cand_tuple[2]
                size_diff = best_cand_tuple[1]
                
                note = "Suggested Match (L2) 💡"
                if size_diff > 5:
                    note += f" [Size Diff: {size_diff}g]"
                
                if len(top_candidates) > 1:
                    note += f" | ⚠️ MULTIPLE MATCHES FOUND: {[c[2]['ITEM'] for c in top_candidates]}"
                
                match_info.update({
                    'Matched_Item': best_cand['ITEM'],
                    'Level': "LEVEL_2",
                    'Match_Score': max_score,
                    'Note': note
                })
        
        results.append(match_info)

    df_res = pd.DataFrame(results)
    
    print("\n" + "="*100)
    print("ARNOTT'S (ANTROSS) BRAND VERIFICATION & QA REPORT")
    print("="*100)
    
    # 1. Level 1 Matches
    l1 = df_res[df_res['Level'] == 'LEVEL_1']
    print(f"\n[PHASE 1] LEVEL 1 (UPC MATCH): Found {len(l1)} Matches")
    for _, r in l1.iterrows():
        print(f"  ✅ {r['Article_Description']} ({r['GTIN']})")
        
    # 2. Level 2 Matches (Fuzzy)
    l2 = df_res[df_res['Level'] == 'LEVEL_2']
    print(f"\n[PHASE 2] LEVEL 2 (ATTRIBUTE MATCH): Found {len(l2)} Potential Matches")
    for _, r in l2.iterrows():
        print(f"  💡 {r['Article_Description']} -> {r['Matched_Item']} ({r['Note']})")
        
    # 3. Gaps
    gaps = df_res[df_res['Level'] == 'GAP']
    print(f"\n[PHASE 3] GAPS (NO MATCH): Found {len(gaps)} Issues")
    for _, r in gaps.iterrows():
        print(f"  ❌ {r['Article_Description']} | {r['Note']}")

    # Final Stats
    total = len(df_711)
    matched = len(l1) + len(l2)
    print(f"\n" + "-"*30)
    print(f"FINAL COVERAGE: {round(matched/total*100, 1)}%")
    print(f"-"*30)

    # Export to Excel
    export_path = os.path.join(os.path.dirname(__file__), "exports", "Arnott_Brand_Verification.xlsx")
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    df_res.to_excel(export_path, index=False)
    print(f"\n✅ Results exported to: {export_path}")

if __name__ == "__main__":
    import os
    run_arnotts_qa()
