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

# CORS Configuration - Support direct port access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production - Actual Domains with Ports
        "https://retail.wersel.co.uk:3001",
        "https://www.retail.wersel.co.uk:3001",
        "http://retail.wersel.co.uk:3001",
        "http://www.retail.wersel.co.uk:3001",
        
        "https://retail-api.wersel.co.uk:8080",
        "https://www.retail-api.wersel.co.uk:8080",
        "http://retail-api.wersel.co.uk:8080",
        "http://www.retail-api.wersel.co.uk:8080",
        
        # Production - Without Ports (for future)
        "https://retail.wersel.co.uk",
        "https://www.retail.wersel.co.uk",
        "https://retail-api.wersel.co.uk",
        "https://www.retail-api.wersel.co.uk",
        "http://retail.wersel.co.uk",
        "http://www.retail.wersel.co.uk",
        "http://retail-api.wersel.co.uk",
        "http://www.retail-api.wersel.co.uk",
        
        # Production - Direct IP with Ports
        "http://40.81.140.169:3001",
        "http://40.81.140.169:8080",
        "https://40.81.140.169:3001",
        "https://40.81.140.169:8080",
        
        # Development
        "http://localhost:3001",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    """Get dashboard summary with merge statistics"""
    single_stock_coll = get_collection("SINGLE_STOCK")
    master_coll = get_collection("MASTER_STOCK")
    
    # Count documents in each collection
    single_stock_count = single_stock_coll.count_documents({})
    master_stock_count = master_coll.count_documents({})
    
    # Calculate merge count
    items_merged = single_stock_count - master_stock_count if single_stock_count > master_stock_count else 0
    
    # Get detailed statistics from MASTER_STOCK
    pipeline = [
        {
            "$group": {
                "_id": None,
                "unique_upcs": {"$addToSet": "$UPC"},
                "merged_items": {"$sum": {"$cond": [{"$gt": ["$merged_from_docs", 1]}, 1, 0]}},
                "single_items": {"$sum": {"$cond": [{"$lte": ["$merged_from_docs", 1]}, 1, 0]}},
                "low_confidence_count": {"$sum": {"$cond": [{"$lt": ["$llm_confidence_min", 0.8]}, 1, 0]}}
            }
        }
    ]
    
    result = list(master_coll.aggregate(pipeline))
    
    if result:
        unique_upcs_count = len(result[0].get("unique_upcs", []))
        merged_items = result[0].get("merged_items", 0)
        single_items = result[0].get("single_items", 0)
        low_confidence = result[0].get("low_confidence_count", 0)
    else:
        unique_upcs_count = 0
        merged_items = 0
        single_items = 0
        low_confidence = 0
    
    # Get unique brands count (using original BRAND column)
    unique_brands = master_coll.distinct("BRAND")
    unique_brands_count = len([b for b in unique_brands if b])  # Filter out empty/null brands
    
    return {
        "single_stock_rows": single_stock_count,
        "master_stock_rows": master_stock_count,
        "items_merged": items_merged,
        "unique_upcs": unique_upcs_count,
        "unique_brands": unique_brands_count,
        "merged_items": merged_items,
        "single_items": single_items,
        "low_confidence": low_confidence
    }

@app.get("/dashboard/products")
async def get_products(limit: int = 100, skip: int = 0):
    """Get products with pagination and optimized fields"""
    coll = get_collection("MASTER_STOCK")
    
    # Only return essential fields for list view
    projection = {
        "_id": 0,
        "merge_id": 1,
        "BRAND": 1,
        "ITEM": 1,
        "UPC": 1,
        "merged_from_docs": 1,
        "merge_level": 1,
        "llm_confidence_min": 1,
        "brand": 1,
        "flavour": 1,
        "size": 1
    }
    
    # Use limit and skip for pagination
    products = list(coll.find({}, projection).limit(limit).skip(skip))
    total_count = coll.count_documents({})
    
    return {
        "products": products,
        "total": total_count,
        "limit": limit,
        "skip": skip
    }

@app.get("/dashboard/product/{merge_id}")
async def get_product_detail(merge_id: str):
    coll = get_collection("MASTER_STOCK")
    product = coll.find_one({"merge_id": merge_id}, {"_id": 0})
    return product

@app.get("/dashboard/low-confidence")
async def get_low_confidence(limit: int = 100):
    """Get low confidence products with limit"""
    coll = get_collection("MASTER_STOCK")
    
    # Only return essential fields
    projection = {
        "_id": 0,
        "merge_id": 1,
        "BRAND": 1,
        "ITEM": 1,
        "UPC": 1,
        "llm_confidence_min": 1,
        "brand": 1,
        "flavour": 1
    }
    
    products = list(coll.find(
        {"llm_confidence_min": {"$lt": 0.8}}, 
        projection
    ).limit(limit))
    
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
    """Export MASTER_STOCK collection to Excel with clean columns"""
    coll = get_collection("MASTER_STOCK")
    docs = list(coll.find({}, {"_id": 0}))
    
    if not docs:
        return {"error": "No data to export"}
    
    # Flatten the data
    df = pd.DataFrame(docs)
    
    # Define essential columns to export (remove duplicates and internal fields)
    essential_columns = [
        # Identifiers
        "UPC", "merge_id", "sheet_name",
        
        # LLM Extracted (Clean versions)
        "brand", "flavour", "size", "normalized_item",
        
        # Original Product Info (only if LLM fields don't exist)
        "ITEM", "MANUFACTURER", "Product Segment",
        
        # Attributes
        "Markets", "MPACK", "Facts", 
        
        # Monthly Data (all w/e columns)
        "Dec 23 - w/e 31/12/23",
        "Jan 24 - w/e 31/01/24", "Feb 24 - w/e 29/02/24", "Mar 24 - w/e 31/03/24",
        "Apr 24 - w/e 30/04/24", "May 24 - w/e 31/05/24", "Jun 24 - w/e 30/06/24",
        "Jul 24 - w/e 31/07/24", "Aug 24 - w/e 31/08/24", "Sep 24 - w/e 30/09/24",
        "Oct 24 - w/e 31/10/24", "Nov 24 - w/e 30/11/24",
        "MAT Nov'24",
        
        # Merge Metadata
        "merge_items", "merged_from_docs", "merge_level", "merge_rule",
        "llm_confidence_min"
    ]
    
    # Select only columns that exist in the dataframe
    export_columns = [col for col in essential_columns if col in df.columns]
    df = df[export_columns]
    
    # Format list columns for Excel
    if "merge_items" in df.columns:
        df["merge_items"] = df["merge_items"].apply(lambda x: " | ".join(map(str, x)) if isinstance(x, list) else x)
    if "merged_upcs" in df.columns:
        df["merged_upcs"] = df["merged_upcs"].apply(lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x)
    
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
    import os
    
    # Check if running in production (SSL certificates exist)
    ssl_keyfile = "/etc/letsencrypt/live/retail-api.wersel.co.uk/privkey.pem"
    ssl_certfile = "/etc/letsencrypt/live/retail-api.wersel.co.uk/fullchain.pem"
    
    use_ssl = os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile)
    
    if use_ssl:
        # Production with SSL
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8080,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        # Local development without SSL
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8080
        )

