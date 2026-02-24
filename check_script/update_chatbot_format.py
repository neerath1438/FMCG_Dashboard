
import os

file_path = "backend/chatbot.py"

# Updated content with:
# 1. STRICT Query Prompt (Ignore "Table/JSON" requests here)
# 2. DYNAMIC Answer Prompt (Respect "Table/JSON" requests here)
# 3. Robust Error Handling

new_content = r'''import json
import os
from openai import OpenAI
import httpx
from backend.database import get_collection
import google.generativeai as genai

# OpenAI Client (For Query Understanding & JSON Generation)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx.Client()
)

# Gemini Client (For High-Token Summarization & Analysis)
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def process_chatbot_query(question, session_id="default"):
    """
    Hybrid Chatbot:
    1. Triggers OpenAI to translate User Question -> MongoDB Query (Better JSON adherence).
    2. Fetches Data.
    3. Triggers Gemini (if available) for Answer Generation IF data is large (High Token).
       Otherwise falls back to OpenAI for simple answers.
    """
    master_coll = get_collection("MASTER_STOCK")
    question_lower = question.lower()
    
    # ---------------------------------------------------------
    # 1. HELP / STATIC RESPONSES
    # ---------------------------------------------------------
    if any(keyword in question_lower for keyword in ["what is this", "how to use", "help", "guide", "tutorial", "benefits"]):
        help_text = """**FMCG Chatbot Capabilities:**
1. **Product Search**: "Price of Oreo", "List all Maggi"
2. **Analysis (Gemini)**: "Summarize sales for Biscuits", "Trends in East Malaysia"
3. **Formats**: "Show as Table", "Give me JSON", "List them"
4. **Market Data**: Supports PM, EM, MT, GT, 7-Eleven.
"""
        return {
            "answer": help_text,
            "data": [],
            "query_used": {},
            "result_count": 0,
            "explanation": "Help info"
        }

    # ---------------------------------------------------------
    # 2. QUERY GENERATION (OPENAI)
    # ---------------------------------------------------------
    total_count = master_coll.count_documents({})
    
    # Check if user wants "Analysis" or "Big Trends"
    is_analysis_request = any(w in question_lower for w in ["analyze", "analysis", "trend", "report", "summary", "list all", "show all"])
    query_limit = 100 if is_analysis_request else 20

    system_prompt = f"""You are an AI assistant for an FMCG Product Mastering Platform in Malaysia.
Database: {total_count} products (MongoDB).

### RULES:
1. TRANSLATE Malay/Manglish -> English (biskut->BISCUIT, kopi->COFFEE, etc).
2. MARKET MAPPING: "East Malaysia"->"EM", "Pen Malaysia"->"PM", "7-Eleven"->"Total 7-Eleven".
3. **DO NOT FORMAT YET**: Even if user asks for "Table" or "JSON", DO NOT generate it here. ONLY generate the MongoDB Query.
4. OUTPUT: VALID JSON {{ "query": {{...}}, "limit": {query_limit}, "explanation": "..." }}

### EXAMPLE: "List East Malaysia items in Table"
User: "List items in East Malaysia in Table"
Query: {{
  "query": {{ "Markets": {{ "$regex": "EM", "$options": "i" }} }},
  "limit": 100,
  "explanation": "Searching 'EM' for East Malaysia. Ignoring 'Table' request for now."
}}
"""

    try:
        # Step A: Generate MongoDB Query using OpenAI (Best for JSON)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )
        
        # Parse JSON
        raw_content = resp.choices[0].message.content.strip()
        if raw_content.startswith("```"):
            start = raw_content.find("{")
            end = raw_content.rfind("}")
            if start != -1 and end != -1:
                raw_content = raw_content[start:end+1]

        try:
            result = json.loads(raw_content)
        except json.JSONDecodeError:
            # Fallback if JSON fails
            return {
                "answer": "I understood what you want, but I had trouble searching the database. Please try rephrasing (e.g., 'Show all Oreo items').",
                "data": [],
                "query_used": {},
                "result_count": 0,
                "explanation": "JSON Parsing Error from LLM"
            }

        query = result.get("query", {})
        limit = result.get("limit", 20)
        explanation = result.get("explanation", "")
        
        # Step B: Fetch Data
        data = list(master_coll.find(query).limit(limit))
        for doc in data: doc.pop("_id", None)
        
        # Step C: Generate Answer (Hybrid: Gemini vs OpenAI)
        
        # Prepare Data Summary
        if len(data) > 20: 
            # Too big for OpenAI? Use Gemini if available
            data_str = json.dumps(data, indent=2) # Pass FULL data to Gemini
            use_gemini = True
        else:
            data_str = json.dumps(data[:10], indent=2) # Pass partial to OpenAI
            use_gemini = False

        answer_prompt = f"""Question: {question}
Explanation: {explanation}
Found: {len(data)} items.
Data:
{data_str}

### INSTRUCTIONS:
1. Answer the question based on the Data.
2. **FORMATTING IS CRITICAL**:
   - If user asked for **"Table"**: Output a Markdown Table.
   - If user asked for **"JSON"**: Output a JSON code block.
   - If user asked for **"List"**: Output a bulleted list.
   - Otherwise: Provide a friendly summary.
"""

        if use_gemini and gemini_api_key:
            # ---> USE GEMINI (High Token Capacity)
            gemini_model = genai.GenerativeModel('gemini-pro')
            response = gemini_model.generate_content(answer_prompt)
            answer_text = response.text
             
        else:
            # ---> USE OPENAI (Standard)
            ans_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": answer_prompt}]
            )
            answer_text = ans_resp.choices[0].message.content

        return {
            "answer": answer_text,
            "data": data,
            "query_used": query,
            "result_count": len(data),
            "explanation": explanation
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"answer": f"System Error: {str(e)}", "data": [], "query_used": {}, "result_count": 0, "explanation": "Error"}
'''

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Updated chatbot.py with Table/JSON Support")
