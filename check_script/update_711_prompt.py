
import os

file_path = "backend/chatbot.py"

# This prompt refines the MARKET AWARENESS to include explicit rules for 7-Eleven.
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
       - **Smkt** = "Smkt" (Supermarket).
       - **CVS** / "7-11" / "Seven Eleven" / "7 Eleven" -> "Total 7-Eleven" (This is a MARKET, NOT a Brand).

       **Action**: If the user asks for these regions/channels, you MUST include a search condition for the `Markets` column.
       *Example Query Condition*: `{{ "Markets": {{ "$regex": "Total 7-Eleven", "$options": "i" }} }}`

    3. **BRAND vs MARKET**: 
       - "7-Eleven" is a MARKET, not a BRAND. Do not search for it in the `BRAND` field.

    4. **MULTI-FIELD SEARCH**: Always use `$or` to search `ITEM`, `normalized_item`, and `BRAND`.

    ### CORRECT EXAMPLE:
    User: "Sales for Oreo in 7-Eleven"
    Strategy: "7-Eleven" -> Market "Total 7-Eleven", "Oreo" -> "OREO".
    Query: {{
      "query": {{
        "$and": [
            {{ "$or": [ {{ "ITEM": {{ "$regex": "OREO", "$options": "i" }} }}, {{ "normalized_item": {{ "$regex": "OREO", "$options": "i" }} }} ] }},
            {{ "Markets": {{ "$regex": "Total 7-Eleven", "$options": "i" }} }}
        ]
      }},
      "limit": 20,
      "explanation": "Searching for OREO in 'Total 7-Eleven' market."
    }}

    Return STRICT JSON only.
    """'''

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Define the start and end markers of the block to replace
    start_marker = 'system_prompt = f"""You are an AI assistant for an FMCG'
    end_marker = '"""'
    
    # Check if file already has the PREVIOUS prompt
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Start marker not found!")
        exit(1)
        
    end_idx = content.find(end_marker, start_idx + len(start_marker))
    
    if end_idx == -1:
        print("End marker not found!")
        exit(1)
        
    final_content = content[:start_idx] + new_prompt + content[end_idx + 3:]
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print("Successfully updated chatbot.py for 7-Eleven rule")

except Exception as e:
    print(f"Error: {e}")
