import os
import pandas as pd
import re
import json
from glob import glob
from datetime import datetime
from llm_client import flow2_client

# Configuration
GAP_DATA_DIR = r'D:\Final_Input_and_Output\output_directry\7-ELEVEN_GAP_DATA'
AUDIT_REPORT_DIR = r'D:\Final_Input_and_Output\output_directry\AI_AUDIT_REPORTS'

# Global dictionary to track stop signals for brands
STOP_SIGNALS = {} # {brand_name: bool}

def extract_size_val(text):
    if not text: return 0.0
    match = re.search(r'(\d+(\.\d+)?)', str(text))
    return float(match.group(1)) if match else 0.0

def process_audit_logic(df, brand_name="Uploaded_File"):
    """
    Core logic to analyze a dataframe, finds GAP vs MARKET_HERO potential matches.
    Returns (results, logs)
    """
    logs = []
    def add_log(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")
        print(f"Audit Log: {msg}")

    add_log(f"Starting AI Audit for Brand: {brand_name}")
    
    try:
        gap_items = df[df['Match_Level'] == 'GAP'].to_dict('records')
        hero_items = df[df['Match_Level'] == 'MARKET_HERO'].to_dict('records')
        
        add_log(f"Found {len(gap_items)} GAP items and {len(hero_items)} MARKET_HERO candidates.")

        if not gap_items or not hero_items:
            add_log("No Gaps or Heroes to audit. Skipping.")
            return [], logs

        audit_results = []
        
        for g_item in gap_items:
            # Check for stop signal
            if STOP_SIGNALS.get(brand_name):
                add_log(f"🛑 Stop signal received for {brand_name}. Halting audit.")
                STOP_SIGNALS[brand_name] = False # Reset
                break

            g_desc = g_item.get('Article_Description', '')
            g_size = extract_size_val(g_item.get('7E_Size'))
            
            add_log(f"Analyzing GAP: {g_desc} ({g_size}g)")
            
            # 1. Coarse Filtering (Size ±10g)
            potential_candidates = []
            for h_item in hero_items:
                h_name = h_item.get('ITEM', '')
                h_size = extract_size_val(h_name)
                
                if abs(g_size - h_size) <= 5.0:
                    potential_candidates.append({
                        "id": h_item.get('UPC') or h_item.get('_id'),
                        "name": h_name,
                        "size": h_size
                    })
            
            if not potential_candidates:
                add_log(f"  ↪ No candidates found within ±10g for {g_desc}. Skipping LLM.")
                continue

            add_log(f"  ↪ Found {len(potential_candidates)} size candidates. Sending to AI for Semantic Audit...")

            # 2. LLM Semantic Verify
            system_prompt = """
            You are an FMCG Audit Expert. Compare ONE 7-Eleven product (GAP) against a list of Nielsen Master items (HEROES).
            Identify if any HERO item is logically the same product as the GAP item.
            
            STRICT RULES:
            - Brand must match.
            - Product Series/Sub-brand MUST match (e.g., Tim Tam vs Good Time is NOT a match).
            - Size must be within ±5g.
            - Ignore packaging variations (Box vs Pack) if weight matches.
            
            Return JSON: {"matched": true/false, "match_id": "...", "reason": "..."}
            """
            
            user_msg = f"GAP Item: {g_desc} ({g_size}g)\n\nCandidates:\n" + \
                       "\n".join([f"- ID: {c['id']}, Name: {c['name']} ({c['size']}g)" for c in potential_candidates])
            
            try:
                response = flow2_client.chat_completion(system_prompt, user_msg)
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                
                llm_res = json.loads(response)
                
                if llm_res.get('matched'):
                    match_name = next((c['name'] for c in potential_candidates if str(c['id']) == str(llm_res.get('match_id'))), 'Unknown')
                    add_log(f"  ✅ AI MATCH FOUND: {g_desc} -> {match_name}")
                    audit_results.append({
                        "gap_item": g_desc,
                        "gap_size": g_size,
                        "matched_with": llm_res.get('match_id'),
                        "matched_name": match_name,
                        "reason": llm_res.get('reason'),
                        "candidates": potential_candidates,
                        "7E_Brand": g_item.get('7E_Brand') or brand_name,
                        "7E_Size": g_item.get('7E_Size') or g_size
                    })
                else:
                    add_log(f"  ❌ AI Decision: No Semantic Match for {g_desc}")
            except Exception as e:
                add_log(f"  ⚠️ LLM Error for {g_desc}: {str(e)}")

        add_log(f"AI Audit completed for {brand_name}. {len(audit_results)} matches identified.")
        return audit_results, logs

    except Exception as e:
        add_log(f"Critical Error auditing {brand_name}: {str(e)}")
        return [], logs

def run_ai_audit_on_file(file_path):
    brand_name = os.path.basename(file_path).replace('mapping_analysis_final_', '').replace('.csv', '')
    try:
        df = pd.read_csv(file_path)
        results, logs = process_audit_logic(df, brand_name)
        
        # Save report
        if not os.path.exists(AUDIT_REPORT_DIR):
            os.makedirs(AUDIT_REPORT_DIR)
            
        report_path = os.path.join(AUDIT_REPORT_DIR, f"audit_report_{brand_name}.json")
        with open(report_path, 'w') as f:
            json.dump({
                "brand": brand_name,
                "timestamp": datetime.now().isoformat(),
                "total_gaps_audited": len(results),
                "matches_found": results,
                "logs": logs
            }, f, indent=4)
            
        return {"brand": brand_name, "status": "Completed", "matchesFound": len(results)}
    except Exception as e:
        return {"brand": brand_name, "status": f"Error: {str(e)}", "matchesFound": 0}

def get_audit_diagnostic(gap_desc, gap_size, hero_candidates):
    """
    Generates a high-precision diagnostic report for an AI Audit mismatch.
    Referencing mapping_analysis.py for technical rules.
    """
    try:
        system_prompt = """
        You are an FMCG Audit Expert specialized in GAP vs Market Hero analysis.
        Explain why this GAP item failed to match or why it was matched to a specific Hero.
        
        TECHNICAL RULES (Reference: mapping_analysis.py):
        1. Flavor Conflicts (L46): SALT vs SWEET, PEANUT vs CHEESE, etc.
        2. Brand Specific Rules (L65): Sub-brand enforcement (e.g. OREO MINI vs THINS).
        3. Bidirectional Keywords (L64): Keywords that must exist in BOTH if present in one.
        4. Size Tolerance: Strict ±5g limit (L360).
        5. Exact UPC Match (L127): UPC matches take precedence but still follow basic flavor safety.
        
        TASK:
        1. Analyze the GAP and Hero candidate attributes.
        2. Identify the EXACT conflict (e.g. "GAP has 'CHEESE' flavor while Hero choice has 'PEANUT'").
        3. Determine the 'rule_reference' (e.g. 'mapping_analysis.py:L46' for Flavor Conflicts).
        4. Provide an 'actionable_solution' (e.g. "Add 'PEANUT' as a flavor conflict for this brand at L53").
        
        You MUST return valid JSON:
        {
            "diagnosis": "Detailed technical explanation...",
            "rule_reference": "mapping_analysis.py:LXX",
            "actionable_solution": "Direct instruction for the developer..."
        }
        """
        
        user_msg = f"GAP Item: {gap_desc} ({gap_size}g)\nCandidates:\n{json.dumps(hero_candidates)}"
        
        response = flow2_client.chat_completion(system_prompt, user_msg)
        
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
            
        return json.loads(response)
    except Exception as e:
        return {
            "diagnosis": f"Error generating diagnostic: {str(e)}",
            "rule_reference": "mapping_analysis.py:L90",
            "actionable_solution": "Check mapping rules in validate_match()."
        }

def translate_audit_text(text):
    """
    Translates English audit diagnostic text to technical Tamil.
    """
    if not text: return ""
    try:
        system_prompt = """
        You are a translation expert specializing in FMCG and Audit Data.
        Translate the provided AI Audit diagnostic report into technical Tamil.
        Keep terms like "GAP", "Hero", "UPC", "Brand", "Flavour" in English or phonetical Tamil.
        Tone: Professional and precise.
        """
        translation = flow2_client.chat_completion(system_prompt, text)
        return translation
    except Exception as e:
        return f"Translation Error: {str(e)}"

def audit_all_brands():
    files = glob(os.path.join(GAP_DATA_DIR, "mapping_analysis_final_*.csv"))
    summary = []
    for f in files:
        summary.append(run_ai_audit_on_file(f))
    return summary
