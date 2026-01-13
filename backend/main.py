import sys
import os
from pathlib import Path

# Add the project root to sys.path to allow absolute imports of the 'backend' package
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from backend.processor import process_excel_flow_1
from backend.database import get_collection
from backend.auth import validate_credentials, create_session, verify_session, destroy_session, get_user_info
from pydantic import BaseModel
import io
import pandas as pd
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Optional

app = FastAPI(title="FMCG Product Mastering Platform")

# CORS Configuration from environment variables
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
cors_methods = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
cors_headers = os.getenv("CORS_ALLOW_HEADERS", "Content-Type,Authorization,X-Requested-With").split(",")
cors_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
    allow_methods=cors_methods,
    allow_headers=cors_headers,
    allow_credentials=cors_credentials,
)

# ============ Pydantic Models ============

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    status: str
    session_token: str
    user: dict

class VerifyResponse(BaseModel):
    status: str
    user: dict

# ============ Authentication Endpoints ============

@app.post("/auth/login")
async def login(request: LoginRequest):
    """
    Login endpoint for demo authentication
    Validates credentials and returns session token
    """
    if not validate_credentials(request.email, request.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session_token = create_session(request.email)
    user_info = get_user_info(request.email)
    
    return {
        "status": "success",
        "session_token": session_token,
        "user": user_info
    }

@app.post("/auth/logout")
async def logout(session_token: str = Header(None, alias="X-Session-Token")):
    """
    Logout endpoint - destroys the session
    """
    if not session_token:
        raise HTTPException(status_code=400, detail="No session token provided")
    
    destroyed = destroy_session(session_token)
    
    return {
        "status": "success",
        "message": "Logged out successfully"
    }

@app.get("/auth/verify")
async def verify_auth(session_token: str = Header(None, alias="X-Session-Token")):
    """
    Verify if session token is valid
    Returns user info if valid
    """
    if not session_token:
        raise HTTPException(status_code=401, detail="No session token provided")
    
    user_info = verify_session(session_token)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {
        "status": "success",
        "user": user_info
    }

# ============ Existing Endpoints ============

@app.post("/upload/excel")
async def upload_excel(file: UploadFile = File(...)):
    """Flow 1: UPC-based merging"""
    contents = await file.read()
    results = process_excel_flow_1(io.BytesIO(contents))
    return {"status": "success", "data": results}

@app.post("/process/llm-mastering/{sheet_name}")
async def trigger_llm_mastering(sheet_name: str):
    """Flow 2: LLM-based mastering with marketing keyword removal"""
    from backend.processor import process_llm_mastering_flow_2
    
    try:
        results = process_llm_mastering_flow_2(sheet_name)
        return {
            "status": "success",
            "sheet_name": sheet_name,
            "data": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/dashboard/summary")
async def get_summary():
    master_coll = get_collection("MASTER_STOCK")
    
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_master_products": {"$sum": 1},
                "total_upcs": {"$sum": {"$size": "$merged_upcs"}},
                "low_confidence_count": {"$sum": {"$cond": ["$is_low_confidence", 1, 0]}},
                "total_docs_merged": {"$sum": "$merged_from_docs"}
            }
        }
    ]
    
    result = list(master_coll.aggregate(pipeline))
    summary = result[0] if result else {
        "total_master_products": 0,
        "total_upcs": 0,
        "low_confidence_count": 0,
        "total_docs_merged": 0
    }
    
    return {
        "raw_rows": summary["total_docs_merged"],
        "unique_upcs": summary["total_upcs"],
        "master_products": summary["total_master_products"],
        "low_confidence": summary["low_confidence_count"]
    }

@app.get("/dashboard/products")
async def get_products():
    coll = get_collection("MASTER_STOCK")
    products = list(coll.find({}, {"_id": 0}))
    return products

@app.get("/dashboard/product/{merge_id}")
async def get_product_detail(merge_id: str):
    coll = get_collection("MASTER_STOCK")
    product = coll.find_one({"merge_id": merge_id}, {"_id": 0})
    return product

@app.get("/dashboard/low-confidence")
async def get_low_confidence():
    coll = get_collection("MASTER_STOCK")
    products = list(coll.find({"is_low_confidence": True}, {"_id": 0}))
    return products

@app.post("/chatbot/query")
async def chatbot_query(request: dict):
    """AI Chatbot endpoint for natural language queries"""
    from backend.chatbot import process_chatbot_query
    
    question = request.get("question", "")
    session_id = request.get("session_id", "default")
    
    if not question:
        return {"error": "Question is required"}
    
    try:
        result = process_chatbot_query(question, session_id)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/export/master-stock")
async def export_master_stock():
    """Export MASTER_STOCK collection to Excel"""
    coll = get_collection("MASTER_STOCK")
    docs = list(coll.find({}, {"_id": 0}))
    
    if not docs:
        return {"error": "No data to export"}
    
    # Flatten the data if needed (pandas handles dicts well)
    df = pd.DataFrame(docs)
    
    # Ensure merged_upcs and merge_items are strings for Excel
    if "merged_upcs" in df.columns:
        df["merged_upcs"] = df["merged_upcs"].apply(lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x)
    if "merge_items" in df.columns:
        df["merge_items"] = df["merge_items"].apply(lambda x: " | ".join(map(str, x)) if isinstance(x, list) else x)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='MasterStock')
    
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="master_stock_export.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.post("/database/reset")
async def reset_database():
    """Reset all database collections"""
    try:
        # Use the same database connection as the rest of the app
        from backend.database import db
        
        # Get all collection names
        collections = db.list_collection_names()
        
        # Collections to reset
        collections_to_reset = [
            "SINGLE_STOCK",
            "MASTER_STOCK", 
            "LLM_CACHE_STORAGE"
        ]
        
        # Add all RAW collections
        raw_collections = [c for c in collections if c.endswith("_RAW")]
        collections_to_reset.extend(raw_collections)
        
        # Delete all documents from each collection
        deleted_counts = {}
        for collection_name in collections_to_reset:
            if collection_name in collections:
                result = db[collection_name].delete_many({})
                deleted_counts[collection_name] = result.deleted_count
        
        return {
            "status": "success",
            "message": "Database reset successfully",
            "deleted_counts": deleted_counts,
            "total_deleted": sum(deleted_counts.values())
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

from fastapi.staticfiles import StaticFiles

# Mount exports directory for Chatbot Excel downloads
export_dir = os.path.join(root_dir, "backend", "exports")
os.makedirs(export_dir, exist_ok=True)
app.mount("/exports", StaticFiles(directory=export_dir), name="exports")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

