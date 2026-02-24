import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv
import copy

def normalize_synonyms(text):
    """Normalize common FMCG synonyms to improve fuzzy matching."""
    if not text: return ""
    s = str(text).upper()
    # Add space between letters and numbers
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    
    # Define synonym maps
    syns = {
        "CHOCOLATE": ["COCOA", "CHOC", "CHOCO", "COK"],
        "STRAWBERRY": ["S/BERRY", "SBERRY", "STRWB", "STRW", "S/BERY"],
        "VANILLA": ["VAN", "VNL", "VNLA"],
        "PEANUT": ["PNUT", "PNT", "P-NUT"],
        "NEAPOLITAN": ["NPLTNE", "NAPOLITANER"],
        "ASSORTED": ["ASST", "ASSTD", "MIX"],
        "CHOCOLATE CHIP": ["C/CHIP", "CHOC CHIP", "CHIP", "CHOC CHIPS"],
        "SALTED CARAMEL": ["SALTED CRMEL", "SALT CRMEL", "SALTED CARAMEL"],
        "MACADAMIA": ["MCDAMIA", "MACDAMIA"],
        "CRANBERRY": ["CRNBER", "CRNBERRIES", "CRNBERY"],
        "BLACKCURRANT": ["B/CURR", "BCURR", "BLACKCURR"],
        "GRAM": ["GM", "GMS", "G"],
        "BISCUIT": ["BISCUITS", "COOKIES", "COOKIE", "SNACK", "SNACKS", "STICK", "STICKS", "STIX"],
    }
    for primary, aliases in syns.items():
        for alias in aliases:
            # Use regex to replace whole word only to avoid partial matches
# 🚨 WORD BOUNDARY GUARD (\b) prevents 'CARAMELISED' matching 'CARAMEL'
            s = re.sub(rf'\b{alias}\b', primary, s)
    return s

def apply_guards(item, data):
    """Apply rule-layer guards to extracted data."""
    if not data: return False
    original_data = copy.deepcopy(data)
    
    # 1. Brand-First Protection
    trimmed_item = item.strip().upper()
    if trimmed_item.startswith("ORI "):
        if not data.get("brand") or data["brand"] in ["ORIGINAL", "UNKNOWN", ""]:
            data["brand"] = "ORI"
            if data.get("flavour") == "ORI":
                data["flavour"] = "NORMAL"
    
    if "APPLE MONKEY" in trimmed_item:
        if not data.get("brand") or data["brand"] in ["ORG", "UNKNOWN", ""]:
            data["brand"] = "APPLE MONKEY"

    # 2. Compound Flavour Protection (Force check for common missed compounds)
    compounds = [
        "SALTED CARAMEL", "SALT CARAMEL", "DARK CHOCOLATE", "WHITE CHOCOLATE", 
        "MILK CHOCOLATE", "CHOCOLATE CHIP", "SEA SALT CHOC CHIP",
        "BUTTER CARAMEL", "CARAMELISED ONION", "SALTED SAVOURY", "NEAPOLITAN",
        "SALTED EGG", "COOKIES & CREAM", "COOKIES AND CREAM", "DOUBLE CHOC",
        "DOUBLE CHOCOLATE", "SOUR CREAM & ONION", "SOUR CREAM AND ONION", 
        "SALTED VANILLA", "CHUNKY HAZELNUT", "PEACH YOGURT", "SOY SAUCE", 
        "CHOCO MELON SEED", "KOKO KRUNCH", "COLORRICE", "MELON SEED",
        "ORGANIC HAZELNUT", "CHIA SEED", "CHOC & CHOC", "VANILLA WHITE",
        "SEA SALT", "SEA SALT BUTTER", "PEANUT BUTTER", "EXTRA LIGHT",
        "EX.LIGHT", "DARK CHOCO BLUEBERRY", "BLUEBERRY", "CRANBERRY", "CRANBERY",
        "NUTTY CHOCO", "NUTTY CHOCOLATE", "BLACKCURRANT", "STRAWBERRY & BLACKCURRANT"
    ]
    
    clean_raw = normalize_synonyms(item).upper()
    for cp in compounds:
        if cp in clean_raw:
            if str(data.get("flavour", "")).upper() != cp:
                data["flavour"] = cp
                break

    # 4. Specific mapping for GPR / ROYAL BRITISH / GPR
    if "GPR" in clean_raw or "ROYAL BRITISH" in clean_raw:
        if "BEAR" in clean_raw:
            data["variant"] = "BEAR FILLING"
        elif "MCOAT" in clean_raw or "M COAT" in clean_raw:
            data["variant"] = "MCOATY"
        elif "SHORTBREAD" in clean_raw:
            data["variant"] = "SHORTBREAD"

    # 5. Basic Flavour Restoration (MISS PROTECTION)
    basic_flavours = [
        "STRAWBERRY", "CHOCOLATE", "VANILLA", "CHEESE", "BUTTER", "ALMOND", 
        "HAZELNUT", "LEMON", "DURIAN", "PINEAPPLE", "COFFEE", "ORANGE", 
        "EGG", "COCOA", "BBQ", "SESAME", "SEAWEED", "PANDAN", "WALNUT", "HONEY",
        "OATS", "RAISIN", "PEACH", "YOGURT", "FUNGUS", "SCALLOP", "MAZOLA",
        "SUNFLOWER", "COLORRICE", "MELON SEED", "KOKO KRUNCH", "OAT"
    ]

    current_flv = str(data.get("flavour", "")).upper()
    if current_flv in ["NORMAL", "UNKNOWN", "", "NONE", "OAT", None]:
        for bf in basic_flavours:
            if bf in clean_raw:
                if current_flv == "OAT" and bf == "OAT": continue
                data["flavour"] = bf
                break

    # 6. Skinny Baker Special Protection
    if "SKINNY BAKER" in clean_raw:
        if "CARAMEL" in clean_raw: data["flavour"] = "SALTED CARAMEL"
        if "ALMOND" in clean_raw: data["flavour"] = "ALMOND"
        if "CRANBER" in clean_raw: data["flavour"] = "CRANBERRY"
        if "MACADAMIA" in clean_raw: data["flavour"] = "MACADAMIA"

    # 3. Brand Overrides (For specific missed brands)
    if "ALL TIME" in clean_raw:
        if not data.get("brand") or data["brand"] in ["NONE", "UNKNOWN", ""]:
            data["brand"] = "ALL TIME"

    # 4. Specific mapping for PNUT/NPLTNE if LLM missed them
    if "PNUT" in trimmed_item or "PNT" in trimmed_item:
        if data.get("flavour") in ["NORMAL", "UNKNOWN", "", "NONE", "CHOCOLATE"]: # Expanded override
            data["flavour"] = "PEANUT"
    if "NPLTNE" in trimmed_item:
        if data.get("flavour") in ["NORMAL", "UNKNOWN", "", "NONE", "CHOCOLATE"]:
            data["flavour"] = "NEAPOLITAN"

    # 5. Basic Flavour Restoration (For missed single flavours)
    basic_flavours = [
        "STRAWBERRY", "CHOCOLATE", "VANILLA", "CHEESE", "BUTTER", "ALMOND", 
        "HAZELNUT", "LEMON", "DURIAN", "PINEAPPLE", "COFFEE", "ORANGE", 
        "EGG", "COCOA", "BBQ", "SESAME", "SEAWEED", "PANDAN", "WALNUT", "HONEY",
        "OAT", "OATS", "RAISIN", "PEACH", "YOGURT", "FUNGUS", "SCALLOP", "MAZOLA",
        "SUNFLOWER", "KOKO KRUNCH", "COLORRICE", "MELON SEED"
    ]
    # Check if generic or if priority keyword is present
    if data.get("flavour") in ["NORMAL", "UNKNOWN", "", "NONE", None] or \
       any(kw in clean_raw for kw in ["OAT", "KOKO KRUNCH", "MELON SEED", "COLORRICE"]):
        for bf in basic_flavours:
            if bf in clean_raw:
                if data.get("flavour") != bf:
                    data["flavour"] = bf
                    break
            
    return data != original_data

def audit_cache():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    collection_name = "LLM_CACHE_STORAGE"
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    
    print(f"Scanning cache: {collection_name}...")
    cursor = collection.find({})
    
    total = collection.count_documents({})
    updated = 0
    checked = 0
    
    for doc in cursor:
        item = doc.get("item")
        data = doc.get("result")
        
        if not item or not data:
            continue
            
        checked += 1
        original_flavour = data.get("flavour")
        original_brand = data.get("brand")
        
        if apply_guards(item, data):
            # Update in MongoDB
            collection.update_one({"_id": doc["_id"]}, {"$set": {"result": data}})
            updated += 1
            print(f"Updated: '{item}'")
            print(f"  Brand: {original_brand} -> {data.get('brand')}")
            print(f"  Flavour: {original_flavour} -> {data.get('flavour')}")
            
    print(f"\nAudit Complete.")
    print(f"Total checked: {checked}/{total}")
    print(f"Total updated: {updated}")
    client.close()

if __name__ == "__main__":
    audit_cache()
