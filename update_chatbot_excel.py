
import os

file_path = "backend/chatbot.py"

# New content with Excel Export logic
# 1. Imports pandas, uuid
# 2. Saves Data to Excel
# 3. Appends Link

new_content = r'''import json
import os
import uuid
import pandas as pd
from openai import OpenAI
import httpx
from backend.database import get_collection
import google.generativeai as genai

# OpenAI Client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx.Client()
)

# Gemini Client
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def process_chatbot_query(question, session_id="default"):
    """
    Hybrid Chatbot with Excel Export:
    1. OpenAI -> Query
    2. MongoDB -> Data
    3. Pandas -> Excel (backend/exports)
    4. Gemini/OpenAI -> Answer + Link
    """
    master_coll = get_collection("MASTER_STOCK")
    question_lower = question.lower()
    
    # 1. HELP RESPONSE
    if any(keyword in question_lower for keyword in ["what is this", "how to use", "help", "guide", "tutorial", "benefits"]):
        return {
            "answer": "This is the FMCG Chatbot. Ask me about prices, sales, or trends. I can also export data to Excel!",
            "data": [],
            "query_used": {},
            "result_count": 0,
            "explanation": "Help info"
        }

    # 2. QUERY GENERATION
    total_count = master_coll.count_documents({})
    is_analysis_request = any(w in question_lower for w in ["analyze", "analysis", "trend", "report", "summary", "list all", "show all"])
    query_limit = 100 if is_analysis_request else 20

    system_prompt = f"""You are an AI assistant for an FMCG Product Mastering Platform in Malaysia.
Database: {total_count} products (MongoDB).

### RULES:
1. TRANSLATE Malay/Manglish -> English (biskut->BISCUIT, etc).
2. MARKET MAPPING: "East Malaysia"->"EM", "Pen Malaysia"->"PM", "7-Eleven"->"Total 7-Eleven".
3. **DO NOT FORMAT**: Only generate the Query JSON.
4. OUTPUT: VALID JSON {{ "query": {{...}}, "limit": {query_limit}, "explanation": "..." }}

### EXAMPLE: "List East Malaysia items"
User: "List items in East Malaysia"
Query: {{
  "query": {{ "Markets": {{ "$regex": "EM", "$options": "i" }} }},
  "limit": 100,
  "explanation": "Searching 'EM' for East Malaysia."
}}
"""

    try:
        # Step A: OpenAI Query Generation
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )
        
        raw_content = resp.choices[0].message.content.strip()
        if raw_content.startswith("```"):
            start = raw_content.find("{")
            end = raw_content.rfind("}")
            if start != -1 and end != -1:
                raw_content = raw_content[start:end+1]

        try:
            result = json.loads(raw_content)
        except json.JSONDecodeError:
            return {
                "answer": "I understood what you want, but I had trouble searching the database. Please try rephrasing.",
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
        
        # Step C: EXCEL EXPORT (The New Feature)
        download_link = ""
        if data:
            try:
                # Create filename
                filename = f"chat_export_{uuid.uuid4().hex[:8]}.xlsx"
                # Ensure directory exists (Assuming script runs from backend root or relative path works)
                export_path = os.path.join("backend", "exports", filename)
                
                # Make dataframe
                df = pd.DataFrame(data)
                
                # Clean list columns for Excel
                for col in df.columns:
                    if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
                         df[col] = df[col].astype(str)

                # Save
                with pd.ExcelWriter(export_path, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                # Create Markdown Link
                # Note: Nginx proxies /api/exports -> backend/exports ? No.
                # In main.py we mounted app.mount("/exports")
                # So URL is http://backend:8000/exports/filename
                # Through Nginx (Frontend): /api/exports/filename
                download_link = f"\n\n[📥 **Download Excel Report**](/api/exports/{filename})"
            except Exception as e:
                print(f"Export Error: {e}")

        # Step D: Generate Answer
        if len(data) > 20: 
            data_str = json.dumps(data, indent=2)
            use_gemini = True
        else:
            data_str = json.dumps(data[:10], indent=2)
            use_gemini = False

        answer_prompt = f"""Question: {question}
Explanation: {explanation}
Found: {len(data)} items.
Data:
{data_str}

### INSTRUCTIONS:
1. Answer the question based on the Data.
2. If user asked for Table, use Markdown Table.
3. Keep it summary-focused if data is large.
"""

        if use_gemini and gemini_api_key:
            gemini_model = genai.GenerativeModel('gemini-pro')
            response = gemini_model.generate_content(answer_prompt)
            answer_text = response.text
        else:
            ans_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": answer_prompt}]
            )
            answer_text = ans_resp.choices[0].message.content
        
        # Append Link
        final_answer = answer_text + download_link

        return {
            "answer": final_answer,
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

print("Updated chatbot.py with Excel Export")
