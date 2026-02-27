import os
import re
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# --- Configuration ---
MONGODB_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017") # Keep using env var for URI
DB_NAME = "fmcg_mastering"
COL_7E = "7-eleven_data"
COL_MASTER = "master_stock_data"
COL_RESULTS = "mapping_results"

def connect_db():
    """Connects to MongoDB and returns the database and collections."""
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    return db, db[COL_7E], db[COL_MASTER], db[COL_RESULTS]

# --- Constants & Rules ---
# Synonyms for better mapping coverage (7E -> Master)
VARIANT_SYNONYMS = {
    "ORIGINAL": ["PLAIN", "REGULAR", "NONE", "NA"],
    "PLAIN": ["ORIGINAL", "REGULAR", "NONE", "NA"],
    "REGULAR": ["ORIGINAL", "PLAIN", "NONE", "NA"],
}

BRAND_SYNONYMS = {
    "CDBRY": ["CADBURY"],
    "CADBURY": ["CDBRY"],
    "H.SENG": ["HUP SENG"],
    "HUP SENG": ["H.SENG"],
    "HS": ["HUP SENG"],
    "JULIE": ["JULIES", "JULIE'S"],
    "JULIES": ["JULIE", "JULIE'S"],
    "JULIE'S": ["JULIE", "JULIES"],
    "HUNTLEY & PALMERS": ["HUNTLEY & PALMER", "HUNTLEY"],
    "HUNTLEY & PALMER": ["HUNTLEY & PALMERS", "HUNTLEY"],
}

FLAVOUR_CONFLICTS = [
    "SALTED CARAMEL", "DARK CHOCOLATE", "DARK CHOCO", "D.CHOC", "D.CHOCO", "NUTTY CHOCO",
    "CHIA SEED", "CHOCOLATE CHIP", "CHOC CHIP", "RED VELVET",
    "MACADAMIA", "PISTACHIO", "HAZELNUT", "HAZEL", "CRANBERRY", "ALMOND",
    "BLUEBERRY", "STRAWBERRY", "PINEAPPLE", "APPLE", "LEMON",
    "COCONUT", "PEANUT BUTTER", "PEANUT", "GOJI", "RAISIN", "MATCHA",
    "VANILLA", "SALTED", "CHOCOLATE", "CHEESE", "BUTTER", "ORIGINAL", "CHEDDAR",
    "BANANA", "ORANGE", "CREAMY", "MILK", "TIRAMISU", "BBQ",
    "MOCHA", "MINT", "CHEESECAKE", "NEAPOLITAN", "BIRTHDAY", "LYCHEE", "FIZZY",
    "POKEMON", "BLACKPINK", "JAVA", "BROWNIE", "MUDCAKE", "RASPBERRY"
]

# Brand-Specific Mapping Rules
# Use normalized brand as key (e.g., "JULIES")
# Rules: 
#   - SUB_BRANDS: List of variants/sub-brands that must match exactly.
#   - BIDIRECTIONAL_KEYWORDS: List of keywords that if present in one, must be in both.
BRAND_RULES = {
    "JULIES": {
        "SUB_BRANDS": ["COCORO", "LOVE LETTERS", "ONE BITE", "ONE GRAB", "OAT 25", "LEMOND", "CHARM", "CHOCO MORE"],
        "BIDIRECTIONAL_KEYWORDS": ["PEANUT", "CHEESE", "SANDWICH", "OAT", "LEMOND", "COCORO"]
    },
    "OREO": {
        "SUB_BRANDS": ["THINS", "MINI", "WAFER ROLL", "DOUBLE STUF", "SELECTION BOX", "DUTCH COCOA", "DUTCH WAFER"],
        "BIDIRECTIONAL_KEYWORDS": ["THINS", "MINI", "GOLDEN", "MOONCAKE", "LYCHEE", "ICE CREAM", "FIZZY", "WAFER ROLL", "POKEMON", "BLACKPINK", "DUTCH"]
    }
}

GENERIC_KEYWORDS = ["CHOCOLATE", "WAFER", "CREAM", "ROLLS", "CRACKER", "BISCUIT", "SANDWICH", "BUTTER", "STICKS", "STIX"]

def validate_match(item_7e_desc, master_doc, detected_flavour_7e, detected_sub_brand_7e, brand_7e, is_upc_match=False):
    """
    Returns True if the match is valid based on flavor and sub-brand guards.
    """
    m_item = normalize_text(master_doc.get("ITEM") or "")
    m_var = normalize_text(master_doc.get("variant") or "")
    m_full = f"{m_item} {m_var}"
    
    # Get Brand Specific Rules (if any)
    norm_br = normalize_text(brand_7e)
    # Check for synonyms in Brand Rules
    rules = BRAND_RULES.get(norm_br)
    if not rules:
        # Check synonyms
        for br_key, syns in BRAND_SYNONYMS.items():
            if norm_br in syns or norm_br == br_key:
                rules = BRAND_RULES.get(br_key)
                break
    
    # 1. Block Flavor Conflicts
    flavours_7e = [fl for fl in FLAVOUR_CONFLICTS if fl in item_7e_desc]
    if detected_flavour_7e != "NA" and detected_flavour_7e not in flavours_7e:
        flavours_7e.append(detected_flavour_7e)
        
    flavours_m = [fl for fl in FLAVOUR_CONFLICTS if fl in m_full]
    
    generic_flavs = ["CHOCOLATE", "CREAMY", "MILK", "ORIGINAL", "NA", "NONE"]
    specific_7e = [f for f in flavours_7e if f not in generic_flavs]
    specific_m = [f for f in flavours_m if f not in generic_flavs]
    
    # Conflict check: Both specific flavors must overlap
    if specific_7e and specific_m:
        if not any(f in specific_m for f in specific_7e):
            return False
            
    # Block specific flavor matching generic (and vice versa) for higher accuracy
    # EXCEPTION: If it is an exact UPC match, we allow it (trust the code)
    if not is_upc_match:
        if (specific_7e and not specific_m) or (not specific_7e and specific_m):
            return False
    
    # Special: Peanut vs Cheese Safety
    if "PEANUT" in flavours_7e and "CHEESE" in flavours_m: return False
    if "CHEESE" in flavours_7e and "PEANUT" in flavours_m: return False
    
    # 2. Sub-brand Enforcement (Dynamic)
    # If it's a UPC match, we trust the code and bypass this strict guard
    target_sbs = rules.get("SUB_BRANDS", []) if rules else []
    m_sub_brand = next((sb for sb in target_sbs if sb in m_full), None)
    if not is_upc_match and detected_sub_brand_7e and m_sub_brand:
        sb_map = {"LOVE LETTER": "LOVE LETTERS", "ONE GRAB": "ONE GRAB", "ONE BITE": "ONE BITE", "OAT 25": "OAT-25", "LEMOND": "LE-MOND", "ONE GRABS": "ONE GRAB", "ONE BITES": "ONE BITE"}
        s7 = sb_map.get(detected_sub_brand_7e, detected_sub_brand_7e)
        sm = sb_map.get(m_sub_brand, m_sub_brand)
        if s7 != sm:
            return False
    
    # 3. Mandatory Keyword Presence (Brand Specific)
    # If it's a UPC match, we trust the code and bypass this strict guard
    if rules and not is_upc_match:
        for sb in rules.get("SUB_BRANDS", []):
            if sb in item_7e_desc and sb not in m_full:
                sb_clean = sb.replace(" ", "").replace("-", "")
                m_full_clean = m_full.replace(" ", "").replace("-", "").replace("CHCO", "CHOCO")
                if sb_clean not in m_full_clean:
                    return False
                
    # 4. Bidirectional Keyword Isolation (Safety Guard - Brand Specific)
    # If it's a UPC match, we bypass this to allow naming variations
    if rules and not is_upc_match:
        for hard_kw in rules.get("BIDIRECTIONAL_KEYWORDS", []):
            if hard_kw in m_full and hard_kw not in item_7e_desc:
                # Special case for Sandwich abbreviation
                if hard_kw == "SANDWICH" and "SWICH" in m_full: continue
                return False
            if hard_kw in item_7e_desc and hard_kw not in m_full:
                if hard_kw == "SANDWICH" and "SWICH" in item_7e_desc: continue
                return False

    return True

def normalize_text(text):
    """Standardizes text: uppercase, removes extra spaces, handles None and punctuation."""
    if not text:
        return "NA"
    text = str(text).upper().strip()
    
    # Remove common brand prefixes/prefixes that cause mismatches
    text = re.sub(r"^(NESTLE|FERRERO|ARN_)\s+", "", text)
    
    # Remove punctuation for cleaner matching (e.g. MCVITIE'S -> MCVITIES)
    text = re.sub(r"[^\w\s]", "", text)
    
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    
    if text in ["NONE", "NORMAL", "", "NA"]:
        return "NA"
    return text

def parse_size(size_str):
    """Extracts numeric value from size string (e.g., '300G' -> 300.0)."""
    if not size_str:
        return 0.0
    size_str = str(size_str).upper().replace("GM", "G")
    match = re.search(r"(\d+(\.\d+)?)", size_str)
    if match:
        return float(match.group(1))
    return 0.0

def parse_mat(doc, key_pattern=r"MAT\s+[A-Za-z]+'?\d+"):
    """Safely parses the latest possible MAT value from a document."""
    # Priority 1: Check if 'MAT Oct'24' or similar exists
    # Find all keys matching MAT pattern and pick the latest one (sorted)
    mat_keys = [k for k in doc.keys() if re.search(key_pattern, k)]
    if not mat_keys:
        return 0.0
    
    # Sort keys to pick the latest (Nov > Oct etc is tricky by string, but usually there's one main one)
    # For now, pick the first match if multiple exist, or refine sorting
    latest_key = sorted(mat_keys, reverse=True)[0] 
    mat_val = doc.get(latest_key)
    
    if not mat_val:
        return 0.0
    try:
        clean_val = str(mat_val).replace(",", "").replace("%", "").replace("$", "").strip()
        return float(clean_val)
    except:
        return 0.0

def levenshtein_similarity(s1, s2):
    """Calculates Levenshtein similarity between two strings (0.0 to 1.0)."""
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

def get_nielsen_lookup(coll_master):
    """Creates lookup dictionaries for Nielsen Master Stock."""
    print("Building Nielsen Master Stock lookup...")
    lookup_attr = {}
    lookup_upc = {}
    
    for doc in coll_master.find():
        brand = normalize_text(doc.get("BRAND"))
        variant = normalize_text(doc.get("VARIANT") or doc.get("variant") or doc.get("flavour"))
        mpack = normalize_text(doc.get("MPACK"))
        upc = str(doc.get("UPC")).strip()
        
        if upc:
            lookup_upc[upc] = doc
        
        # Primary key mapping
        key = (brand, variant, mpack)
        if key not in lookup_attr:
            lookup_attr[key] = []
        lookup_attr[key].append(doc)
        
        # Brand-only grouping for smart fallback
        brand_key_str = f"BRAND_ONLY_{(brand, mpack)}"
        if brand_key_str not in lookup_attr:
            # We use a special prefix to distinguish brand-only lists
            lookup_attr[brand_key_str] = []
        lookup_attr[brand_key_str].append(doc)

    return lookup_upc, lookup_attr

def run_mapping():
    db, coll_7e, coll_master, coll_results = connect_db()
    
    # Clear previous results
    coll_results.delete_many({})
    print("Previous results cleared.")
    
    # 1. Load Data
    upc_lookup_n, attr_lookup_n = get_nielsen_lookup(coll_master)
    seven_eleven_docs = list(coll_7e.find())
    print(f"Starting mapping for {len(seven_eleven_docs)} 7-Eleven Articles...")
    
    # Pre-calculate unique brands for fuzzy matching performance
    master_keys = list(attr_lookup_n.keys()) # (Brand, Var, MPack)
    unique_b_n = list(set([k[0] for k in master_keys]))
    
    # Track matched Master IDs for bi-directional gap analysis
    matched_master_ids = set()
    
    results = []
    count = 0
    for item_7e in seven_eleven_docs:
        count += 1
        if count % 500 == 0:
            print(f"  Processed {count}/{len(seven_eleven_docs)}...")
        
        gtin = str(item_7e.get("GTIN"))
        # Normalize GTIN for comparison (handle 13-digit vs 8-digit)
        gtin_clean = re.sub(r"^0+", "", gtin)
        
        brand_7e = normalize_text(item_7e.get("L4_Description_Brand"))
        variant_7e = normalize_text(item_7e.get("7E_Variant"))
        flavour_7e = normalize_text(item_7e.get("7E_flavour") or "NA")
        size_7e = parse_size(item_7e.get("7E_Nrmsize"))
        mpack_7e = normalize_text(item_7e.get("7E_MPack") or "X1")

        # Prepare strong detection keywords BEFORE UPC Match
        full_desc_7e = normalize_text(item_7e.get("ArticleDescription") or "")
        desc_clean = normalize_text(item_7e.get("ArticleDescription") or "")
        desc_keywords = [w for w in desc_clean.split() if len(w) > 2 and w not in ["JULIES", "JULIE'S", "BISCUIT"]]
        
        # Determine relevant sub-brands for the target brand
        target_br_norm = normalize_text(brand_7e)
        target_sbs = []
        # Check synonyms
        if target_br_norm in BRAND_RULES:
            target_sbs = BRAND_RULES[target_br_norm].get("SUB_BRANDS", [])
        else:
            for br_key, syns in BRAND_SYNONYMS.items():
                if target_br_norm in syns or target_br_norm == br_key:
                    target_sbs = BRAND_RULES.get(br_key, {}).get("SUB_BRANDS", [])
                    break
                    
        strong_7e = [kw for kw in desc_keywords if kw in target_sbs or kw in FLAVOUR_CONFLICTS]
        detected_sub_brand_7e = next((sb for sb in target_sbs if sb in full_desc_7e), None)
        detected_flavour_7e = next((fl for fl in FLAVOUR_CONFLICTS if fl in full_desc_7e), flavour_7e)

        potential_nielsen = []
        
        # --- Search Level 1: UPC Match (Flexible) ---
        if gtin:
            # Try exact match
            if gtin in upc_lookup_n:
                match_cand = upc_lookup_n[gtin]
                if validate_match(full_desc_7e, match_cand, detected_flavour_7e, detected_sub_brand_7e, brand_7e, is_upc_match=True):
                    potential_nielsen.append(match_cand)
            # Try suffix match (STRICTER: Require at least 10 digits for suffix to avoid accidental short overlap)
            elif len(gtin_clean) >= 10:
                found_match = None
                for u_n in upc_lookup_n.keys():
                    u_n_clean = re.sub(r"^0+", "", u_n)
                    if len(u_n_clean) >= 10 and (gtin_clean.endswith(u_n_clean) or u_n_clean.endswith(gtin_clean)):
                        cand = upc_lookup_n[u_n]
                        if validate_match(full_desc_7e, cand, detected_flavour_7e, detected_sub_brand_7e, brand_7e, is_upc_match=True):
                            found_match = cand
                            break
                if found_match:
                    potential_nielsen.append(found_match)
        
        if not potential_nielsen:
            search_brands = [brand_7e] + BRAND_SYNONYMS.get(brand_7e, [])
            search_variants = [variant_7e] + VARIANT_SYNONYMS.get(variant_7e, [])
            
            for br in search_brands:
                # 1. Standard Attribute Match
                for vr in search_variants:
                    key = (br, vr, mpack_7e)
                    potential_matches = attr_lookup_n.get(key, [])
                    for m in potential_matches:
                        m_size = parse_size(m.get("NRMSIZE") or m.get("size"))
                        if abs(m_size - size_7e) <= 5.0:
                            if validate_match(full_desc_7e, m, detected_flavour_7e, detected_sub_brand_7e, brand_7e):
                                if m not in potential_nielsen:
                                    potential_nielsen.append(m)

                # 2. Smart Fallback for "NONE/NA/NONE" variants
                if not potential_nielsen and (variant_7e == "NA" or variant_7e == "NONE" or flavour_7e != "NA" or "NONE" in variant_7e):
                    brand_only_key = f"BRAND_ONLY_{(br, mpack_7e)}"
                    pattern_matches = attr_lookup_n.get(brand_only_key, [])
                    
                    for m in pattern_matches:
                        m_size = parse_size(m.get("NRMSIZE") or m.get("size"))
                        if abs(m_size - size_7e) <= 5.0:
                            if validate_match(full_desc_7e, m, detected_flavour_7e, detected_sub_brand_7e, brand_7e):
                                # For fallback, we ALSO want some keyword overlap
                                m_full = normalize_text(f"{m.get('ITEM')} {m.get('variant')}")
                                matched_kws = [kw for kw in desc_keywords if kw in m_full]
                                has_strong_match = any(kw in strong_7e for kw in matched_kws)
                                
                                if has_strong_match or len(matched_kws) >= 2:
                                    if m not in potential_nielsen:
                                        potential_nielsen.append(m)

        # Try 3: Fuzzy Brand Fallback (MPack MUST still match)
        if not potential_nielsen and brand_7e != "NA" and len(brand_7e) > 3:
            best_brand = None
            best_score = 0
            for b_n in unique_b_n:
                score = levenshtein_similarity(brand_7e, b_n)
                if score > best_score:
                    best_score = score
                    best_brand = b_n
            
            if best_score >= 0.85:
                # Still check variant or fallback with the fuzzy brand
                brand_only_key = f"BRAND_ONLY_{(best_brand, mpack_7e)}"
                matches = attr_lookup_n.get(brand_only_key, [])
                for m in matches:
                    m_size = parse_size(m.get("NRMSIZE") or m.get("size"))
                    if abs(m_size - size_7e) <= 5.0:
                        if validate_match(full_desc_7e, m, detected_flavour_7e, detected_sub_brand_7e, brand_7e):
                            if m not in potential_nielsen:
                                potential_nielsen.append(m)

        # 2. Results Preparation
        match_level = "GAP"
        match_type = "No Match Found"
        best_nielsen = None
        
        if potential_nielsen:
            potential_nielsen.sort(key=lambda x: parse_mat(x), reverse=True)
            best_nielsen = potential_nielsen[0]
            matched_master_ids.add(best_nielsen.get("_id"))
            
            if any(str(m.get("UPC")).strip().lstrip('0') == gtin_clean for m in potential_nielsen):
                match_level = "LEVEL_1"
                match_type = "Exact/Flexible UPC Match"
            else:
                match_level = "LEVEL_2"
                match_type = "Attribute/Flavour Match"

        mapping_upcs = "; ".join(list(set(str(m.get("UPC")) for m in potential_nielsen if m.get("UPC"))))
        mapping_items = "; ".join(list(set(str(m.get("ITEM")) for m in potential_nielsen if m.get("ITEM"))))
        
        # Prepare results in the specific order requested by the user
        res_dict = {
            "UPC": best_nielsen.get("UPC") if best_nielsen else None,
            "ITEM": best_nielsen.get("ITEM") if best_nielsen else None,
            "Main_UPC": best_nielsen.get("UPC") if best_nielsen else None,
            "UPC_GroupName": mapping_items,
            "ArticleCode": item_7e.get("ArticleCode"),
            "GTIN": gtin,
            "Article_Description": item_7e.get("ArticleDescription"),
            # Remaining context fields
            "Source": "7-Eleven",
            "7E_Brand": item_7e.get("L4_Description_Brand"),
            "7E_Variant": item_7e.get("7E_Variant"),
            "7E_Flavour": item_7e.get("7E_flavour"),
            "7E_Size": item_7e.get("7E_Nrmsize"),
            "Match_Level": match_level,
            "Match_Type": match_type,
            "Matched_MAT": best_nielsen.get("MAT Nov'24") if best_nielsen else 0,
            "MAPPING_UPC": mapping_upcs
        }
        results.append(res_dict)

    # --- Search Level 4: Market Gaps (Extra Master Items) ---
    print("Finding Market Gaps (Extra items in Nielsen)...")
    total_market_mat = 0
    matched_market_mat = 0
    
    # Pre-calculate total market MAT and matched MAT
    for doc in coll_master.find():
        mat_val = parse_mat(doc)
        total_market_mat += mat_val
        if doc.get("_id") in matched_master_ids:
            matched_market_mat += mat_val

    for doc in coll_master.find():
        if doc.get("_id") not in matched_master_ids:
            results.append({
                "UPC": doc.get("UPC"),
                "ITEM": doc.get("ITEM"),
                "Main_UPC": doc.get("UPC"),
                "UPC_GroupName": doc.get("ITEM"),
                "ArticleCode": "NEW",
                "GTIN": doc.get("UPC"),
                "Article_Description": "Extra item in Market",
                # Context
                "Source": "Master Stock (Market Gap)",
                "7E_Brand": doc.get("BRAND"),
                "7E_Variant": doc.get("VARIANT"),
                "7E_Flavour": doc.get("flavour"),
                "7E_Size": doc.get("size") or doc.get("NRMSIZE"),
                "Match_Level": "MARKET_HERO",
                "Match_Type": "Available in Market Only",
                "Matched_MAT": parse_mat(doc),
                "MAPPING_UPC": doc.get("UPC")
            })

    if results:
        coll_results.insert_many(results)
        print(f"Mapping complete. {len(results)} total entry records created.")
        
        # Pass coverage stats to report
        metrics = {
            "total_market_mat": total_market_mat,
            "matched_market_mat": matched_market_mat
        }
        generate_qa_report(coll_results, metrics)

def generate_qa_report(coll_results, metrics=None):
    print("\n--- Bi-Directional QA Report ---")
    total_7e = coll_results.count_documents({"Source": "7-Eleven"})
    l1_matches = coll_results.count_documents({"Match_Level": "LEVEL_1"})
    l2_matches = coll_results.count_documents({"Match_Level": "LEVEL_2"})
    gaps_7e = coll_results.count_documents({"Match_Level": "GAP"})
    market_heroes = coll_results.count_documents({"Match_Level": "MARKET_HERO"})
    
    matched = l1_matches + l2_matches
    
    print(f"Total 7-Eleven Articles: {total_7e}")
    print(f"Level 1 Matches (UPC):  {l1_matches}")
    print(f"Level 2 Matches (Attr): {l2_matches}")
    print(f"7-Eleven Gaps:          {gaps_7e}")
    print(f"Market Hero Gaps:       {market_heroes}")
    print(f"7E Item Coverage:       {round(matched/total_7e*100, 2) if total_7e else 0}%")
    
    if metrics:
        t_mat = metrics.get("total_market_mat", 0)
        m_mat = metrics.get("matched_market_mat", 0)
        val_cov = (m_mat / t_mat * 100) if t_mat else 0
        print(f"Market Value Coverage:  {round(val_cov, 2)}% (Value Share covered by 7E)")
        print(f"Matched Market MAT:     {round(m_mat, 2)}")
        print(f"Total Market MAT:       {round(t_mat, 2)}")
    
    print("-" * 33)

def export_results():
    """Exports mapping results to an Excel file."""
    db, _, _, coll_results = connect_db()
    data = list(coll_results.find())
    if not data:
        print("No results to export.")
        return
    
    df = pd.DataFrame(data)
    if '_id' in df.columns:
        df.drop(columns=['_id'], inplace=True)
    
    # Sort columns to ensure the specific order requested
    req_cols = ["UPC", "ITEM", "Main_UPC", "UPC_GroupName", "ArticleCode", "GTIN", "Article_Description"]
    # Filter only columns that actually exist in the dataframe to avoid errors
    actual_req = [c for c in req_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in actual_req]
    df = df[actual_req + other_cols]
    
    filename_xlsx = "Mapping_Analysis_Export.xlsx"
    filename_csv = "Mapping_Analysis_Export.csv"
    
    try:
        df.to_excel(filename_xlsx, index=False)
        df.to_csv(filename_csv, index=False)
        print(f"Exported to {filename_xlsx} and {filename_csv}")
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        alt_xlsx = f"Mapping_Analysis_Export_{timestamp}.xlsx"
        alt_csv = f"Mapping_Analysis_Export_{timestamp}.csv"
        df.to_excel(alt_xlsx, index=False)
        df.to_csv(alt_csv, index=False)
        print(f"WARNING: Permission denied. Exported to {alt_xlsx} and {alt_csv}")

if __name__ == "__main__":
    run_mapping()
    export_results()
