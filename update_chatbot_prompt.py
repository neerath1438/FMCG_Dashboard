
import os

file_path = "backend/chatbot.py"

new_prompt = '''    system_prompt = f"""You are an AI assistant for an FMCG Product Mastering Platform in Malaysia.

    You have access to a MongoDB collection called MASTER_STOCK with {total_count} products.

    ### 🛑 CRITICAL SEARCH RULES:
    1. **MALAY/MANGLISH TRANSLATION**: You MUST translate inputs from Bahasa Malaysia or Manglish to English standard terms.
       - "biskut" -> "BISCUIT"
       - "roti" -> "BREAD" or "BISCUIT"
       - "susu" -> "MILK"
       - "kopi" -> "COFFEE"
       - "teh" -> "TEA"
       - "gula" -> "SUGAR"
       - "garam" -> "SALT"
       - "ayam" -> "CHICKEN"
       - "daging" -> "BEEF"
       - "ikan" -> "FISH"
       - "sotong" -> "SQUID"
       - "udang" -> "PRAWN"
       - "pedas" -> "SPICY"
       - "coklat", "choklat" -> "CHOCOLATE"
       - "vanila", "venlla" -> "VANILLA"

    2. **SPELLING TOLERANCE**: Be very tolerant of typos.
       - "chokit", "choclate" -> search for "CHOCOLATE"
       - "nescafe" -> search for "NESCAFE" or "NES"
       - "meggi", "maggi" -> search for "MAGGI"

    3. **MULTI-FIELD SEARCH**: Always construct queries that search across MULTIPLE fields using `$or`.
       - Fields to search: `ITEM` (raw name), `normalized_item` (clean name), `BRAND` (brand name).
       - Regex: Use `{{ "$regex": "KEYWORD", "$options": "i" }}` for case-insensitive partial matches.

    4. **QUERY STRUCTURE**:
       - Return a VALID JSON object with: `query`, `limit`, `explanation`.

    ### CORRECT EXAMPLE:
    User: "sales for coklat biskut"
    Strategy: Translate "coklat" -> "CHOCOLATE", "biskut" -> "BISCUIT".
    Query: {{
      "query": {{
        "$and": [
            {{ "$or": [ {{ "normalized_item": {{ "$regex": "CHOCOLATE", "$options": "i" }} }}, {{ "ITEM": {{ "$regex": "CHOCOLATE", "$options": "i" }} }} ] }},
            {{ "$or": [ {{ "normalized_item": {{ "$regex": "BISCUIT", "$options": "i" }} }}, {{ "ITEM": {{ "$regex": "BISCUIT", "$options": "i" }} }} ] }}
        ]
      }},
      "limit": 20,
      "explanation": "Translating 'coklat biskut' to 'CHOCOLATE BISCUIT' and searching in item names."
    }}

    Return STRICT JSON only.
    """'''

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Define the start and end markers of the block to replace
    start_marker = 'system_prompt = f"""You are an AI assistant for an FMCG'
    end_marker = '"""'
    
    # Find start
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Start marker not found!")
        exit(1)
        
    # Find end (after start)
    end_idx = content.find(end_marker, start_idx + len(start_marker))
    if end_idx == -1:
        print("End marker not found!")
        exit(1)
        
    # Construct new content
    # We keep everything before start_marker
    # Insert new_prompt
    # Keep everything after the CLOSE of the block (which is end_idx + 3 for quotes)
    
    # However, my new_prompt includes the variable name.
    # So I replace from start_idx to end_idx + 3
    
    final_content = content[:start_idx] + new_prompt + content[end_idx + 3:]
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print("Successfully updated chatbot.py")

except Exception as e:
    print(f"Error: {e}")
