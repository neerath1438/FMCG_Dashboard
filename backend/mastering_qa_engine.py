import os
import pandas as pd
import re
import json
import io
from datetime import datetime
from llm_client import flow2_client
from backend.database import get_collection

# Configuration
MASTERING_REPORT_DIR = r'D:\Final_Input_and_Output\output_directry\MASTERING_QA_REPORTS'

# Global dictionary to track stop signals for brands
STOP_SIGNALS = {} # {brand_name: bool}

def extract_size_val(text):
    if not text: return 0.0
    # Clean up text to find numbers followed by g/ml etc
    match = re.search(r'(\d+(\.\d+)?)', str(text))
    return float(match.group(1)) if match else 0.0

def process_mastering_logic(df, brand_name="Master_Stock"):
    """
    Identifies potential groups in Master Stock report for items that didn't merge.
    Focuses on merged_document_from == 1.
    Strict Rules: Same Facts, Markets, Size, and MPack.
    Semantic Logic: ITEM description synonyms.
    """
    logs = []
    def add_log(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")
        print(f"Mastering Log: {msg}")

    add_log(f"Starting Mastering QA for: {brand_name}")
    
    try:
        # 1. Filter targets (items that are currently single)
        # Handle different potential column names including the ones provided by user
        merge_col = None
        for c in ['duplicate_documents', 'MERGED_FROM_DOCS', 'merged_document_from', 'MergedCount', 'count']:
            if c in df.columns:
                merge_col = c
                break
        
        if not merge_col:
            add_log(f"Error: Single-item count column not found. Checked: ['MERGED_FROM_DOCS', 'merged_document_from']. Found: {list(df.columns)}")
            return [], logs

        # Cast to numeric to be safe
        df[merge_col] = pd.to_numeric(df[merge_col], errors='coerce').fillna(0)
        singles = df[df[merge_col] == 1].copy()
        
        add_log(f"Found {len(singles)} single items ({merge_col} == 1) out of {len(df)} total rows.")
        
        if len(singles) < 2:
            add_log("Not enough single items to identify groups. Skipping.")
            return [], logs

        # 2. Bucketing by Strict Rules
        # Column lookup helper (case insensitive + specific matches)
        def find_col(possible_names):
            for name in possible_names:
                # Try exact match first
                if name in df.columns: return name
                # Try case-insensitive
                for col in df.columns:
                    if col.upper() == name.upper(): return col
            return None

        mpack_col = find_col(['MPACK', 'mpack'])
        item_col = find_col(['ITEM', 'Item', 'Description', 'NORMALIZED_ITEM'])
        facts_col = find_col(['FACTS', 'Facts', 'facts'])
        markets_col = find_col(['MARKETS', 'Markets', 'markets'])
        size_col = find_col(['SIZE', 'Size', 'size']) # Use SIZE column directly if possible

        if not all([mpack_col, item_col, facts_col, markets_col]):
            add_log(f"Missing required columns (ITEM, MPACK, FACTS, or MARKETS). Found: {list(df.columns)}")
            return [], logs

        # Bucket key = (Facts, Markets, Size, MPack)
        buckets = {}
        for idx, row in singles.iterrows():
            # Priority: Use SIZE column, fallback to regex extraction from ITEM
            raw_size = str(row.get(size_col, '')).strip() if size_col else ""
            if raw_size:
                # Some sizes are "40G", "40.0", "40 GM" - normalize to float
                size_val = extract_size_val(raw_size)
            else:
                size_val = extract_size_val(str(row.get(item_col, '')))
                
            key = (
                str(row.get(facts_col, '')).strip(),
                str(row.get(markets_col, '')).strip(),
                size_val,
                str(row.get(mpack_col, 'X1')).strip().upper()
            )
            if key not in buckets:
                buckets[key] = []
            buckets[key].append({
                "id": str(idx),
                "item": str(row.get(item_col, '')),
                "orig_row": row.to_dict()
            })

        # Sort items within each bucket to ensure consistent index mapping for AI
        for key in buckets:
            buckets[key].sort(key=lambda x: x['item'])

        add_log(f"Partitioned singles into {len(buckets)} strict buckets (Facts+Markets+Size+MPack).")
        
        suggested_groups = []
        
        # 3. Analyze Buckets with >= 2 items using AI
        for key, items in buckets.items():
            if len(items) < 2:
                continue
            
            # Check for stop signal
            if STOP_SIGNALS.get(brand_name):
                add_log(f"🛑 Stop signal received for {brand_name}. Halting audit loop.")
                STOP_SIGNALS[brand_name] = False # Reset for next run
                break
            
            facts, market, size, mpack = key
            add_log(f"Analyzing Bucket: {market} | {facts} | {size}g | {mpack} ({len(items)} items)")
            
            system_prompt = f"""
            You are an FMCG Data Expert. Analyze product descriptions (ITEM) from a strictly matched bucket:
            Bucket Context: Market({market}), Size({size}g), MPack({mpack}).
            
            GOAL: Identify which items are logically identical (synonyms or naming variations).
            
            STRICT RULES:
            1. ONLY merge if items are 100% the same product but with different text (e.g., "Choc" vs "Chocolate").
            2. DO NOT merge different flavours or variants (e.g., Strawberry vs Berry Yogurt).
            3. DO NOT merge different series (e.g., "Pocky Stick" vs "Pocky Crushed Fruit").
            4. If in doubt, DO NOT merge.
            5. Provide a confidence score (0-100). We only accept high confidence.
            
            Return JSON in this format:
            {{
              "potential_groups": [
                {{
                  "group_name": "Shared canonical name",
                  "item_indices": [index from provided list],
                  "reason": "Why these are a match",
                  "confidence": 0-100
                }}
              ]
            }}
            """
            
            user_msg = "Items in Bucket:\n" + \
                       "\n".join([f"{i}. {item['item']}" for i, item in enumerate(items)])
            
            try:
                response = flow2_client.chat_completion(system_prompt, user_msg)
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                
                ai_res = json.loads(response)
                
                groups = ai_res.get('potential_groups', [])
                for gp in groups:
                    # User rule: Show only >= 75% confidence
                    if gp.get('confidence', 0) >= 75 and len(gp.get('item_indices', [])) >= 2:
                        matched_items = [items[idx]['item'] for idx in gp['item_indices'] if idx < len(items)]
                        add_log(f"  ✅ High Confidence Group ({gp['confidence']}%): '{gp['group_name']}'")
                        suggested_groups.append({
                            "group_name": gp['group_name'],
                            "bucket_info": {
                                "market": market,
                                "facts": facts,
                                "size": size,
                                "mpack": mpack
                            },
                            "matched_items": matched_items,
                            "reason": gp['reason'],
                            "confidence": gp['confidence']
                        })
                    elif gp.get('confidence', 0) < 75 and len(gp.get('item_indices', [])) >= 2:
                        add_log(f"  ℹ️ Skipping Group '{gp['group_name']}' due to low confidence ({gp['confidence']}%).")
            except Exception as e:
                add_log(f"  ⚠️ AI Error for bucket {key}: {str(e)}")

        add_log(f"Mastering QA completed. Identified {len(suggested_groups)} high-confidence groups.")
        return suggested_groups, logs

    except Exception as e:
        add_log(f"Critical Error in Mastering QA: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return [], logs

def run_mastering_audit(file_path):
    brand_name = os.path.basename(file_path).split('.')[0]
    try:
        # Handle Excel or CSV
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
            
        results, logs = process_mastering_logic(df, brand_name)
        
        # Save report
        if not os.path.exists(MASTERING_REPORT_DIR):
            os.makedirs(MASTERING_REPORT_DIR)
            
        report_path = os.path.join(MASTERING_REPORT_DIR, f"mastering_report_{brand_name}.json")
        with open(report_path, 'w') as f:
            json.dump({
                "brand": brand_name,
                "timestamp": datetime.now().isoformat(),
                "groups_found": results,
                "logs": logs
            }, f, indent=4)
            
        return {"brand": brand_name, "status": "Completed", "groupsFound": len(results), "report": report_path}
    except Exception as e:
        return {"brand": brand_name, "status": f"Error: {str(e)}", "groupsFound": 0}

def get_mastering_diagnostic(item_names):
    """
    Simulates Flow 2 decision logic to explain why items didn't merge.
    """
    if not item_names: return "No items provided."
    
    try:
        cache_coll = get_collection("LLM_CACHE_STORAGE")
        # Fetch attributes from cache
        cache_docs = list(cache_coll.find({"item": {"$in": item_names}}))
        
        # Map item -> result
        results_map = {doc['item']: doc['result'] for doc in cache_docs}
        
        # Build comparison summary for AI
        comparison_text = "Comparison of AI Extracted Attributes:\n"
        for it in item_names:
            res = results_map.get(it, {"status": "Not Found in Cache"})
            comparison_text += f"- ITEM: {it}\n  Attributes: {json.dumps(res)}\n\n"
            
        system_prompt = """
        You are an FMCG Data Expert specializing in 'Flow 2' product mastering. 
        Explain why these items failed to merge in the main pipeline.
        
        FLOW 2 DECISION GATES (Reference: processor.py):
        1. Confidence Gate: LLM_CONFIDENCE_THRESHOLD = 0.92 (L23). 
        2. Attribute Match: Brand, Product Line (Family), Product Form, and Flavour/Variant must match 100%.
        3. Size Gate: Sizes must be identical.
        4. Rule Guards: 
           - 'Synonyms' defined in normalize_synonyms() starting at L49.
           - GLICO/POCKY logic at L1122.
           - HWA TAI logic at L1106.
           - OREO logic at L898.
        
        TASK:
        1. Analyze the provided LLM attributes.
        2. Identify the EXACT mismatch.
        3. Determine the 'rule_reference' (e.g. 'processor.py:L1122' or 'processor.py:L49').
        4. Provide an 'actionable_solution' that specifically mentions what to add and where (e.g. "Add 'FAMILY SET' to the synonyms list in processor.py:L88").
        
        You MUST return valid JSON in this format:
        {
            "diagnosis": "Detailed explanation of the mismatch...",
            "rule_reference": "processor.py:LXX",
            "actionable_solution": "Direct instruction on what to change..."
        }
        """
        
        user_msg = f"Items to Diagnose:\n{comparison_text}"
        
        response = flow2_client.chat_completion(system_prompt, user_msg)
        
        # Clean JSON response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
            
        try:
            return json.loads(response)
        except:
            # Fallback if AI fails to return JSON
            return {
                "diagnosis": response,
                "rule_reference": "processor.py:L1122",
                "actionable_solution": "Please check the attribute mapping rules."
            }
    except Exception as e:
        return f"Diagnostic Error: {str(e)}"
def translate_diagnostic_text(text):
    """
    Translates English diagnostic text to technical Tamil using AI.
    """
    if not text: return ""
    
    try:
        system_prompt = """
        You are a translation expert specializing in FMCG and Data Science.
        Translate the provided English diagnostic report into technical Tamil.
        
        RULES:
        1. Keep technical terms like "Item", "Confidence", "Brand", "Flavour", "Size", "Rule Guards" as is or in phonetical Tamil.
        2. Ensure the tone is professional but helpful.
        3. Use a clear and precise technical Tamil vocabulary.
        
        Output format: Simple text paragraphs in Tamil.
        """
        
        translation = flow2_client.chat_completion(system_prompt, text)
        return translation
    except Exception as e:
        return f"Translation Error: {str(e)}"
