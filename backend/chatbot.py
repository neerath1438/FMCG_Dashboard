import json
import os
from openai import OpenAI
import httpx
from backend.database import get_collection

from datetime import datetime
from backend.database import get_collection
from backend.llm_client import llm_client

# Path for Domain Knowledge
DOMAIN_KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), "CHATBOT_DOMAIN_KNOWLEDGE.txt")

def get_learning_context():
    """Fetch corrections and domain knowledge."""
    knowledge = ""
    if os.path.exists(DOMAIN_KNOWLEDGE_PATH):
        with open(DOMAIN_KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
            knowledge = f.read()

    
    # Fetch verified corrections
    learning_coll = get_collection("CHATBOT_LEARNING")
    corrections = list(learning_coll.find().limit(10))
    learning_str = "\n### RECENT LEARNINGS & CORRECTIONS:\n"
    for c in corrections:
        learning_str += f"- Question: {c.get('question')}\n  Correct Query: {json.dumps(c.get('correction'))}\n"
    
    return knowledge + learning_str

def log_interaction(question, result, data_count):
    """Log to CHATBOT_HISTORY for future training."""
    history_coll = get_collection("CHATBOT_HISTORY")
    history_coll.insert_one({
        "timestamp": datetime.now(),
        "question": question,
        "query": result.get("query"),
        "answer": result.get("answer"),
        "result_count": data_count,
        "is_verified": False
    })

def process_chatbot_query(question, session_id="default"):
    """
    Simplified OpenAI-Powered Chatbot:
    1. OpenAI -> Query + Sort
    2. MongoDB -> Data (with sort)
    3. OpenAI -> Natural Language Answer
    """
    master_coll = get_collection("MASTER_STOCK")
    question_lower = question.lower()
    
    # 1. HELP RESPONSE
    if any(keyword in question_lower for keyword in ["what is this", "how to use", "help", "guide", "tutorial", "benefits"]):
        return {
            "answer": "This is the FMCG Chatbot. I can help you search for products, analyze sales trends, and find specific items in the database.",
            "data": [],
            "query_used": {},
            "result_count": 0,
            "explanation": "Help info"
        }

    # 2. QUERY GENERATION
    total_count = master_coll.count_documents({})
    is_analysis_request = any(w in question_lower for w in ["analyze", "analysis", "trend", "report", "summary", "list all", "show all", "top"])
    query_limit = 100 if is_analysis_request else 20

    learning_context = get_learning_context()
    system_prompt = f"""You are an AI assistant for an FMCG Product Mastering Platform in Malaysia.
Database: {total_count} products (MongoDB).

{learning_context}

### SCHEMA (CASE SENSITIVE):
- `BRAND`: (e.g., 'OREO', 'GLICO', 'RITZ')
- `Markets`: (e.g., 'Pen Malaysia', 'EM', 'Total 7-Eleven')
- `Facts`: (e.g., 'Sales Value', 'Sales Units')
- `ITEM`: Product descriptions.
- `MAT Nov'24`: Numeric value for sorting (Sales).
- `merged_from_docs`: Number of items combined into this master record.
- `merge_items`: Array of original product names.
- `sheet_name`: The source file name (e.g., 'Nielsen_Wersel_Test').

### RULES:
1. **QUERY**: Return a MongoDB query. ALWAYS use the exact field names above.
2. **MARKET MAPPING**: "Malaysia" usually refers to `{"Markets": "Pen Malaysia"}`.
3. **TECHNICAL INPUT**: If the user provides a piece of Code or MongoDB query fragment, incorporate that logic into the generated query.
4. **PRIORITY**: If asked about "merging" or "what items are combined", search inside the "merge_items" array.
5. **SALES**: For "top", "best", "total sales" queries, ALWAYS use {{"Facts": "Sales Value"}} and sort by "MAT Nov'24": -1.
6. **MERGED COUNT**: For "top merged", "highest consolidation", or "most items combined" queries, sort by "merged_from_docs": -1.
7. **TABULAR DATA**: If the user asks for a "table", "summary", or "sales breakdown", the **Answer Generation** (Step C) MUST use professional Markdown table format.
   Example: | Market | Brand | Merged Count | Item |
8. **NO EMPTY ANSWERS**: If a specific brand is not found, try searching for keywords in the ITEM field using regex.
9. **OUTPUT**: ALWAYS return ONLY a VALID JSON object.
   Expected Structure: {{ "query": {{...}}, "sort": [[...]], "limit": {query_limit}, "explanation": "..." }}
"""



    try:
        # Step A: OpenAI Query Generation (Using llm_client for Azure Claude)
        raw_content = llm_client.chat_completion(
            system_prompt=system_prompt,
            user_message=question,
            temperature=0
        )
        
        raw_content = raw_content.strip()
        # Find the outermost { } to extract JSON even if there's surrounding text
        start = raw_content.find("{")
        end = raw_content.rfind("}")
        if start != -1 and end != -1:
            raw_content = raw_content[start:end+1]

        try:
            result = json.loads(raw_content)
        except json.JSONDecodeError:
            return {
                "answer": "I understood your technical request, but I had trouble formatting the database command properly. Please try asking in plain English (e.g., 'Show me Oreo items with more than one UPC').",
                "data": [],
                "query_used": {},
                "result_count": 0,
                "explanation": f"JSON Parsing Error. Raw: {raw_content[:100]}"
            }

        query = result.get("query", {})
        limit = result.get("limit", 20)
        sort_list = result.get("sort", [])
        explanation = result.get("explanation", "")
        
        # Step B: Fetch Data with Sort
        mongo_cursor = master_coll.find(query)
        if sort_list:
            mongo_cursor = mongo_cursor.sort(sort_list)
        
        data = list(mongo_cursor.limit(limit))
        for doc in data: doc.pop("_id", None)
        
        # Step C: Generate Answer
        data_str = json.dumps(data[:20], indent=2) # Send sample for answer

        answer_prompt = f"""Question: {question}
Explanation: {explanation}
Found: {len(data)} items.
Data (Sample):
{data_str}

### INSTRUCTIONS:
1. Answer the question based on the Data in a natural, conversational way.
2. **PRECISION**: If the user asks for a "Count" or "Total Number", give that number clearly. **STRICT RULE**: In this case, YOUR ENTIRE ANSWER MUST BE NO MORE THAN 2 SENTENCES. Do not list details.
3. If no data was found, EXPLAIN WHY.
4. Always try to be helpful. If you see similar items in the database that might be what the user wants, suggest them (unless it's a count query).
5. If no data is found, suggest checking the spelling or trying a broader brand search.
"""



        # Step C: Generate Answer (Using llm_client)
        answer_text = llm_client.chat_completion(
            system_prompt="You are a helpful FMCG Data assistant.", # Simpler prompt context
            user_message=answer_prompt,
            temperature=0.7
        )
        
        final_response = {
            "answer": answer_text,
            "data": data,
            "query_used": query,
            "result_count": len(data),
            "explanation": explanation
        }
        
        # Step D: Log for Training
        log_interaction(question, final_response, len(data))
        
        return final_response

    except Exception as e:
        import traceback
        print(f"CRITICAL CHATBOT ERROR: {e}")
        traceback.print_exc()
        return {
            "answer": "I'm sorry, I'm having a bit of trouble accessing the database right now. Please try asking your question again in a moment, or try a simpler search term.",
            "data": [],
            "query_used": {},
            "result_count": 0,
            "explanation": f"System Error: {str(e)}"
        }


