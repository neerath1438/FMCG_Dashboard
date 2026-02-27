import pandas as pd
import re

def normalize_text(text):
    if not text: return ""
    return str(text).strip().upper()

def parse_size(size_str):
    if not size_str: return 0.0
    size_str = str(size_str).upper().replace('GM', 'G')
    match = re.search(r'(\d+(\.\d+)?)', size_str)
    if match:
        return float(match.group(1))
    return 0.0

def get_keywords(text):
    # Clean and split into meaningful words
    text = re.sub(r'[^A-Z0-9\s]', ' ', normalize_text(text))
    words = text.split()
    # Remove common words
    ignore = ['ARNOTTS', 'ARNOTT', 'S', 'BRAND', 'BISCUITS', 'CRACKER', 'ORIGINAL']
    return [w for w in words if w not in ignore and len(w) > 2]

def run_arnotts_verification():
    path_711 = r'd:\git\FMCG_Dashboard\ARNOTTS_7-ELEVEN_RAW.xlsx'
    path_nielsen = r'd:\git\FMCG_Dashboard\ARNOTTS_BRAND_RAW.xlsx'
    
    df_711 = pd.read_excel(path_711)
    df_nielsen = pd.read_excel(path_nielsen)
    
    # Pre-process Nielsen
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
            '7E_Article': desc,
            '7E_GTIN': gtin,
            'Nielsen_Item': "GAP",
            'Nielsen_UPC': "NA",
            'Level': "GAP",
            'Type': "No Match Found",
            'Recommendation': "Manual Check Needed"
        }
        
        # Level 1: Extra UPC Match
        if gtin in nielsen_upc_map:
            n_row = nielsen_upc_map[gtin]
            match_info.update({
                'Nielsen_Item': n_row['ITEM'],
                'Nielsen_UPC': n_row['UPC_str'],
                'Level': "LEVEL_1",
                'Type': "Exact UPC Match",
                'Recommendation': "Verified ✅"
            })
        else:
            # Level 2: Attribute Match (Fuzzy)
            candidates = []
            for _, n_row in df_nielsen.iterrows():
                # Check keywords overlap
                k_nielsen = get_keywords(n_row['ITEM'])
                common = set(keywords_7e) & set(k_nielsen)
                
                # Check size tolerance (+/- 5g)
                size_diff = abs(n_row['size_val'] - size_7e)
                
                if len(common) >= 1 and size_diff <= 5.0:
                    candidates.append((len(common), n_row))
            
            if candidates:
                # Pick best candidate (most keywords matching)
                candidates.sort(key=lambda x: x[0], reverse=True)
                best_n = candidates[0][1]
                match_info.update({
                    'Nielsen_Item': best_n['ITEM'],
                    'Nielsen_UPC': best_n['UPC_str'],
                    'Level': "LEVEL_2",
                    'Type': "Attribute Match (Fuzzy Keywords + Size)",
                    'Recommendation': "Suggested Match 💡 (Please Verify)"
                })
        
        results.append(match_info)

    # Output Results
    df_res = pd.DataFrame(results)
    
    # Format for readability
    print("\n" + "="*80)
    print("ARNOTT'S BRAND MAPPING VERIFICATION REPORT")
    print("="*80)
    
    # Matched Items
    matched = df_res[df_res['Level'] != 'GAP']
    print(f"\n[SUMMARY] Total 7-Eleven Items: {len(df_711)} | Matched: {len(matched)} | Gaps: {len(df_res)-len(matched)}")
    
    print("\n--- MATCHED ITEMS ---")
    for _, r in matched.iterrows():
        print(f"[{r['Level']}] {r['7E_Article']} -> {r['Nielsen_Item']} ({r['Recommendation']})")
        
    # Gaps
    gaps = df_res[df_res['Level'] == 'GAP']
    if not gaps.empty:
        print("\n--- REMAINING GAPS ---")
        for _, r in gaps.iterrows():
            print(f"[GAP] {r['7E_Article']} (GTIN: {r['7E_GTIN']}) | {r['Recommendation']}")
            # Debugging keywords
            print(f"      Keywords searched: {get_keywords(r['7E_Article'])}")

if __name__ == "__main__":
    run_arnotts_verification()
