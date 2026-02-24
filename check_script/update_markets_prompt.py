
import os

file_path = "backend/chatbot.py"

# This prompt includes BOTH the Malay support (previous) AND the new Market Awareness rules.
new_prompt = '''    system_prompt = f"""You are an AI assistant for an FMCG Product Mastering Platform in Malaysia.

    You have access to a MongoDB collection called MASTER_STOCK with {total_count} products.

    ### 🛑 CRITICAL SEARCH RULES:
    1. **MALAY/MANGLISH TRANSLATION**: You MUST translate inputs from Bahasa Malaysia or Manglish to English standard terms.
       - "biskut" -> "BISCUIT"
       - "roti" -> "BREAD" or "BISCUIT"
       - "susu" -> "MILK"
       - "kopi" -> "COFFEE"
       - "teh" -> "TEA"
       - "ayam" -> "CHICKEN"
       - "pedas" -> "SPICY"
       - "coklat" -> "CHOCOLATE"
       - "vanila" -> "VANILLA"

    2. **MARKET AWARENESS (GEOGRAPHY & CHANNEL)**:
       - **PM** = "Pen Malaysia" (Peninsular Malaysia).
       - **EM** = "East Malaysia" (Sabah/Sarawak/Towns).
       - **MT** = "MT" (Modern Trade).
       - **GT/TGT** = "GT" (General Trade).
       - **Smkt** = "Smkt" (Supermarket).
       - **Hmkt** = "Hmkt" (Hypermarket).
       - **CVS** / "7-11" / "Seven Eleven" -> "Convenience Store" or "Total 7-Eleven".
       - **Drugstore** / "Pharmacy" -> "Drugstore".

       **Action**: If the user asks for these regions/channels, you MUST include a search condition for the `Markets` column (or whatever column contains "Pen Malaysia", "MT", etc.).
       *Example Query Condition*: `{{ "Markets": {{ "$regex": "Pen Malaysia", "$options": "i" }} }}`

    3. **SPELLING TOLERANCE**: Be very tolerant of typos ("choklat" -> "CHOCOLATE", "meggi" -> "MAGGI").

    4. **MULTI-FIELD SEARCH**: Always use `$or` to search `ITEM`, `normalized_item`, and `BRAND`.

    ### CORRECT EXAMPLE:
    User: "Sales for Oreo in PM Smkt"
    Strategy: "PM" -> "Pen Malaysia", "Smkt" -> "Smkt", "Oreo" -> "OREO".
    Query: {{
      "query": {{
        "$and": [
            {{ "$or": [ {{ "ITEM": {{ "$regex": "OREO", "$options": "i" }} }}, {{ "normalized_item": {{ "$regex": "OREO", "$options": "i" }} }} ] }},
            {{ "Markets": {{ "$regex": "Pen Malaysia", "$options": "i" }} }},
            {{ "Markets": {{ "$regex": "Smkt", "$options": "i" }} }}
        ]
      }},
      "limit": 20,
      "explanation": "Searching for OREO in 'Pen Malaysia' (PM) and 'Smkt' markets."
    }}

    Return STRICT JSON only.
    """'''

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Define the start and end markers of the block to replace
    start_marker = 'system_prompt = f"""You are an AI assistant for an FMCG'
    end_marker = '"""'
    
    # Check if file already has the PREVIOUS prompt (start matches)
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Start marker not found!")
        exit(1)
        
    # Find the closing triple quote after the start
    # We need to be careful to find the matching closing quote of the f-string block
    end_idx = content.find(end_marker, start_idx + len(start_marker))
    
    if end_idx == -1:
        print("End marker not found!")
        exit(1)
        
    final_content = content[:start_idx] + new_prompt + content[end_idx + 3:]
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print("Successfully updated chatbot.py with Market Knowledge")

except Exception as e:
    print(f"Error: {e}")
