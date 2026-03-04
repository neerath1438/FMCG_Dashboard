import sys
import os
from pathlib import Path

# Add the project root to sys.path to allow absolute imports of the 'backend' package
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.processor import process_excel_flow_1
from backend.database import get_collection, create_indexes, RAW_DATA_COL, SINGLE_STOCK_COL, MASTER_STOCK_COL
from backend.auth import validate_credentials, create_session, verify_session, destroy_session, get_user_info
from backend.qa_engine import audit_all_brands, process_audit_logic, STOP_SIGNALS as QA_STOP_SIGNALS, get_audit_diagnostic, translate_audit_text
from backend.mastering_qa_engine import process_mastering_logic, STOP_SIGNALS as MASTERING_STOP_SIGNALS, get_mastering_diagnostic, translate_diagnostic_text
from pydantic import BaseModel
import io
import pandas as pd
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="FMCG Product Mastering Platform")

# Create MongoDB indexes on startup for faster upserts
@app.on_event("startup")
async def startup_event():
    print("🚀 Creating MongoDB indexes...")
    create_indexes()

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
        "http://20.0.161.242:3001",
        "http://20.0.161.242:8000",
        "https://20.0.161.242:3001",
        "https://20.0.161.242:8000",
        
        # Development
        "http://localhost:3001",
        "http://localhost:3000",
        "http://localhost:5173",
        # "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # "http://127.0.0.1:8080",
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
async def upload_excel(file: UploadFile = File(...), request: Request = None):
    """
    Flow 1: UPC-based merging with comprehensive validation
    """
    print(f"\n📥 Received upload request: {file.filename}")
    from backend.file_validator import validate_upload_file
    
    try:
        # Check if client is still connected before reading file
        if request and await request.is_disconnected():
            print(f"❌ Aborting: Client disconnected before file read")
            raise HTTPException(status_code=499, detail="Client disconnected")
        
        print(f"⏳ Reading file contents: {file.filename}...")
        # Read file contents
        contents = await file.read()
        print(f"✅ File read complete. Size: {len(contents) / 1024 / 1024:.2f} MB")
        
        # Check again before validation (file read can take time)
        if request and await request.is_disconnected():
            raise HTTPException(status_code=499, detail="Client disconnected during file read")
        
        # Comprehensive validation
        xl, warnings = validate_upload_file(file, contents)
        
        # Final check before expensive processing
        if request and await request.is_disconnected():
            raise HTTPException(status_code=499, detail="Client disconnected before processing")
        
        # Process file (validation passed)
        results = await process_excel_flow_1(io.BytesIO(contents), request=request)
        
        # Return success with warnings if any
        response = {
            "status": "success",
            "data": results,
            "filename": file.filename,
            "sheets_processed": list(results.keys()) if isinstance(results, dict) else []
        }
        
        if warnings:
            response["warnings"] = warnings
        
        return response
        
    except HTTPException:
        # Re-raise validation errors (already have good messages)
        raise
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="Excel file is empty or contains no data. Please add data to your file and try again."
        )
        
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot parse Excel file. The file may be corrupted: {str(e)}"
        )
        
    except Exception as e:
        # Catch-all for unexpected errors with helpful message
        error_msg = str(e)
        if "No such file" in error_msg or "does not exist" in error_msg:
            detail = "File upload failed. Please try again."
        elif "Memory" in error_msg or "memory" in error_msg:
            detail = "File is too large to process. Please reduce file size or split into multiple files."
        else:
            detail = f"Error processing file: {error_msg}"
        
        raise HTTPException(
            status_code=500,
            detail=detail
        )

@app.post("/process/llm-mastering/{sheet_name}")
async def trigger_llm_mastering(sheet_name: str, request: Request = None):
    """Flow 2: LLM-based mastering with marketing keyword removal"""
    from backend.processor import process_llm_mastering_flow_2
    
    try:
        results = await process_llm_mastering_flow_2(sheet_name, request=request)
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
    raw_coll = get_collection(RAW_DATA_COL)
    master_coll = get_collection(MASTER_STOCK_COL)
    
    # Count documents
    raw_data_count = raw_coll.count_documents({})
    master_stock_count = master_coll.count_documents({})
    
    # Calculate merge count (Input Rows - Output Rows)
    items_merged = raw_data_count - master_stock_count if raw_data_count > master_stock_count else 0
    
    # Get unique UPCs count from RAW_DATA to match original file
    unique_upcs = raw_coll.distinct("UPC")
    unique_upcs_count = len([u for u in unique_upcs if u])
    
    # Get unique Brands count from RAW_DATA (original file - to verify AI accuracy)
    # Filter out null, empty strings, and whitespace-only brands
    unique_brands = raw_coll.distinct("BRAND")
    unique_brands_count = len([b for b in unique_brands if b and str(b).strip()])
    
    # Get detailed statistics from MASTER_STOCK for other metrics
    pipeline = [
        {
            "$group": {
                "_id": None,
                "merged_items": {"$sum": {"$cond": [{"$gt": ["$merged_from_docs", 1]}, 1, 0]}},
                "single_items": {"$sum": {"$cond": [{"$lte": ["$merged_from_docs", 1]}, 1, 0]}},
                "low_confidence_count": {"$sum": {"$cond": [{"$lt": ["$llm_confidence_min", 0.8]}, 1, 0]}}
            }
        }
    ]
    
    result = list(master_coll.aggregate(pipeline))
    
    if result:
        merged_items = result[0].get("merged_items", 0)
        single_items = result[0].get("single_items", 0)
        low_confidence = result[0].get("low_confidence_count", 0)
    else:
        merged_items = 0
        single_items = 0
        low_confidence = 0
    
    return {
        "single_stock_rows": raw_data_count, # Returning raw count as "Input Rows"
        "master_stock_rows": master_stock_count,
        "items_merged": items_merged,
        "unique_upcs": unique_upcs_count,
        "unique_brands": unique_brands_count,
        "merged_items": merged_items,
        "single_items": single_items,
        "low_confidence": low_confidence
    }

# @app.get("/api/audit/counts")
# async def get_audit_counts():
#     """Get audit dashboard counts for Nielsen data flow"""
#     # Get collections - using correct collection names
#     raw_data_coll = get_collection("raw_data")  # Raw Nielsen data
#     single_stock_coll = get_collection("single_stock_data")
#     master_stock_coll = get_collection("master_stock_data")
#     seven_eleven_coll = get_collection("7-eleven_data")  # Hyphen, not underscore
#     gaps_coll = get_collection("nielsen_gap_items")
#     seven_eleven_extra_coll = get_collection("7eleven_extra_items")  # No hyphen in 'extra'
#     
#     # Query for Nielsen Malaysia data
#     nielsen_query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
#     
#     # Count documents
#     raw_nielsen = raw_data_coll.count_documents(nielsen_query)  # Raw Nielsen with query
#     single_stock = single_stock_coll.count_documents(nielsen_query)  # Apply same filter
#     master_stock = master_stock_coll.count_documents(nielsen_query)
#     ai_enriched = seven_eleven_coll.count_documents({})
#     
#     # Carried items: 7eleven_extra_items where Article_Description != "NOT CARRIED"
#     carried = seven_eleven_extra_coll.count_documents({"Article_Description": {"$ne": "NOT CARRIED"}})
#     
#     # 7-Eleven Gaps: 7eleven_extra_items where Article_Description = "NOT CARRIED"
#     gaps = seven_eleven_extra_coll.count_documents({"Article_Description": "NOT CARRIED"})
#     
#     # 7-Eleven Unique: AI Enriched - Carried Items (Reverse Gap)
#     seven_eleven_unique = ai_enriched - carried
#     
#     return {
#         "raw_nielsen": raw_nielsen,
#         "single_stock": single_stock,
#         "master_stock": master_stock,
#         "ai_enriched": ai_enriched,
#         "carried": carried,
#         "gaps": gaps,
#         "seven_eleven_unique": seven_eleven_unique
#     }

@app.get("/api/filtered-records")
async def get_filtered_records():
    """Get the 7 records that were filtered out (in raw_data but not in single_stock_data)"""
    raw_data_coll = get_collection("raw_data")
    single_stock_coll = get_collection("single_stock_data")
    
    # Query for Nielsen Malaysia data
    nielsen_query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
    
    # Get all raw_data records with their unique identifiers
    raw_docs = list(raw_data_coll.find(nielsen_query))
    
    # Create a set of unique keys from single_stock_data for comparison
    # Using combination of BRAND, ITEM, VARIANT, MPACK, NRMSIZE as unique key
    single_stock_keys = set()
    for doc in single_stock_coll.find(nielsen_query):
        key = (
            doc.get("BRAND", ""),
            doc.get("ITEM", ""),
            doc.get("VARIANT", ""),
            doc.get("MPACK", ""),
            doc.get("NRMSIZE", "")
        )
        single_stock_keys.add(key)
    
    # Find filtered records (in raw but not in single)
    filtered_docs = []
    for doc in raw_docs:
        key = (
            doc.get("BRAND", ""),
            doc.get("ITEM", ""),
            doc.get("VARIANT", ""),
            doc.get("MPACK", ""),
            doc.get("NRMSIZE", "")
        )
        if key not in single_stock_keys:
            # Convert ObjectId to string for JSON serialization
            doc["_id"] = str(doc["_id"])
            filtered_docs.append(doc)
    
    return {
        "count": len(filtered_docs),
        "records": filtered_docs
    }

@app.get("/api/raw-product/{product_id}")
async def get_raw_product(product_id: str):
    """Get raw product details by ID from raw_data collection"""
    from bson import ObjectId
    
    raw_data_coll = get_collection("raw_data")
    
    try:
        # Convert string ID to ObjectId
        obj_id = ObjectId(product_id)
        product = raw_data_coll.find_one({"_id": obj_id})
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Convert ObjectId to string for JSON serialization
        product["_id"] = str(product["_id"])
        
        return product
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid product ID: {str(e)}")

@app.get("/api/merged-products")
async def get_merged_products():
    """Get all products that were merged (merged_from_docs > 1) for Nielsen Malaysia"""
    master_stock_coll = get_collection("master_stock_data")
    
    # Use OR to handle both Title Case and Uppercase field names with trailing spaces
    # Title Case: "Facts": "Sales Value", "Markets": "Pen Malaysia"
    # Upper Case: "FACTS": "Sales Value ", "MARKETS": "Pen Malaysia           "
    
    # Regex to handle case-insensitivity and trailing spaces
    facts_regex = {"$regex": "^Sales Value", "$options": "i"}
    markets_regex = {"$regex": "^Pen Malaysia", "$options": "i"}
    
    query = {
        "merged_from_docs": {"$gt": 1},
        "$or": [
            {"Facts": facts_regex, "Markets": markets_regex},
            {"FACTS": facts_regex, "MARKETS": markets_regex}
        ]
    }
    
    merged_products = list(master_stock_coll.find(query))
    
    # Convert ObjectId to string for JSON serialization
    for product in merged_products:
        product["_id"] = str(product["_id"])
    
    return {
        "count": len(merged_products),
        "products": merged_products
    }

@app.get("/dashboard/products")
async def get_products(limit: int = 100, skip: int = 0, search: str = None, brand: str = None, confidence_status: str = 'all'):
    """Get products with server-side filtering and pagination"""
    coll = get_collection(MASTER_STOCK_COL)
    
    query = {}
    if brand and brand != 'all':
        # Special handling for UNKNOWN brand - match NULL, empty, or "UNKNOWN"
        if brand == 'UNKNOWN':
            query["$or"] = [
                {"BRAND": {"$exists": False}},
                {"BRAND": None},
                {"BRAND": ""},
                {"BRAND": "UNKNOWN"}
            ]
        else:
            query["BRAND"] = brand
    
    if search:
        query["$or"] = [
            {"ITEM": {"$regex": search, "$options": "i"}},
            {"BRAND": {"$regex": search, "$options": "i"}},
            {"UPC": {"$regex": search, "$options": "i"}}
        ]
    
    # New Confidence Status Filter
    if confidence_status == 'na':
        query["$or"] = [
            {"llm_confidence_min": {"$exists": False}},
            {"llm_confidence_min": None},
            {"llm_confidence_min": 0}
        ]
    elif confidence_status == 'scored':
        query["llm_confidence_min"] = {"$gt": 0}
    
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
        "size": 1,
        "MARKETS": 1,
        "MARKET": 1
    }
    
    products = list(coll.find(query, projection).limit(limit).skip(skip))
    total_count = coll.count_documents(query)
    
    return {
        "products": products,
        "total": total_count,
        "limit": limit,
        "skip": skip
    }

@app.get("/dashboard/brands")
async def get_all_brands():
    """Get list of all unique brands in MASTER_STOCK"""
    coll = get_collection(MASTER_STOCK_COL)
    # Filter out null, empty, or whitespace-only brands for the dropdown/list
    brands = sorted([b for b in coll.distinct("BRAND") if b and str(b).strip()])
    return {"brands": brands}

@app.get("/dashboard/analytics-data")
async def get_analytics_data():
    """Get calculated analytics metrics via aggregation pipelines"""
    master_coll = get_collection(MASTER_STOCK_COL)
    
    # 1. Base Stats
    raw_coll = get_collection(RAW_DATA_COL)
    total_products = master_coll.count_documents({})
    # Filter out null, empty, or whitespace-only brands
    unique_brands_count = len([b for b in master_coll.distinct("BRAND") if b and str(b).strip()])
    
    raw_data_count = raw_coll.count_documents({})
    merged_products_count = raw_data_count - total_products if raw_data_count > total_products else 0
    
    # 2. Avg Confidence and Distribution
    confidence_pipeline = [
        {
            "$group": {
                "_id": None,
                "avg_confidence": {"$avg": "$llm_confidence_min"},
                "conf_90_100": {"$sum": {"$cond": [{"$gte": ["$llm_confidence_min", 0.9]}, 1, 0]}},
                "conf_80_90": {"$sum": {"$cond": [{"$and": [{"$gte": ["$llm_confidence_min", 0.8]}, {"$lt": ["$llm_confidence_min", 0.9]}]}, 1, 0]}},
                "conf_70_80": {"$sum": {"$cond": [{"$and": [{"$gte": ["$llm_confidence_min", 0.7]}, {"$lt": ["$llm_confidence_min", 0.8]}]}, 1, 0]}},
                "conf_60_70": {"$sum": {"$cond": [{"$and": [{"$gte": ["$llm_confidence_min", 0.6]}, {"$lt": ["$llm_confidence_min", 0.7]}]}, 1, 0]}},
                "conf_below_60": {"$sum": {"$cond": [{"$and": [{"$lt": ["$llm_confidence_min", 0.6]}, {"$gt": ["$llm_confidence_min", 0]}]}, 1, 0]}},
                "conf_na": {"$sum": {"$cond": [{"$or": [{"$not": ["$llm_confidence_min"]}, {"$eq": ["$llm_confidence_min", 0]}]}, 1, 0]}}
            }
        }
    ]
    
    conf_res = list(master_coll.aggregate(confidence_pipeline))
    avg_conf = conf_res[0].get("avg_confidence", 0) if conf_res else 0
    
    confidence_dist = [
        {"name": "90-100%", "value": conf_res[0].get("conf_90_100", 0) if conf_res else 0},
        {"name": "80-90%", "value": conf_res[0].get("conf_80_90", 0) if conf_res else 0},
        {"name": "70-80%", "value": conf_res[0].get("conf_70_80", 0) if conf_res else 0},
        {"name": "60-70%", "value": conf_res[0].get("conf_60_70", 0) if conf_res else 0},
        {"name": "Below 60%", "value": conf_res[0].get("conf_below_60", 0) if conf_res else 0},
        {"name": "N/A", "value": conf_res[0].get("conf_na", 0) if conf_res else 0, "isNA": True},
    ]

    # 3. Brand Distribution (Top 10)
    brand_pipeline = [
        {"$group": {"_id": "$BRAND", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {"$project": {"name": "$_id", "value": "$count", "_id": 0}}
    ]
    brand_dist = list(master_coll.aggregate(brand_pipeline))

    # 4. Merge Level Distribution
    merge_pipeline = [
        {
            "$group": {
                "_id": None,
                "single": {"$sum": {"$cond": [{"$lte": ["$merged_from_docs", 1]}, 1, 0]}},
                "merge_2_5": {"$sum": {"$cond": [{"$and": [{"$gt": ["$merged_from_docs", 1]}, {"$lte": ["$merged_from_docs", 5]}]}, 1, 0]}},
                "merge_6_10": {"$sum": {"$cond": [{"$and": [{"$gt": ["$merged_from_docs", 5]}, {"$lte": ["$merged_from_docs", 10]}]}, 1, 0]}},
                "merge_10_plus": {"$sum": {"$cond": [{"$gt": ["$merged_from_docs", 10]}, 1, 0]}}
            }
        }
    ]
    merge_res = list(master_coll.aggregate(merge_pipeline))
    merge_dist = [
        {"name": "Single Item", "value": merge_res[0].get("single", 0) if merge_res else 0},
        {"name": "Merged (2-5)", "value": merge_res[0].get("merge_2_5", 0) if merge_res else 0},
        {"name": "Merged (6-10)", "value": merge_res[0].get("merge_6_10", 0) if merge_res else 0},
        {"name": "Merged (10+)", "value": merge_res[0].get("merge_10_plus", 0) if merge_res else 0},
    ]

    # 5. Top Merged Products
    top_merged = list(master_coll.find(
        {"merged_from_docs": {"$gt": 1}},
        {"_id": 0, "BRAND": 1, "ITEM": 1, "merged_from_docs": 1, "MARKETS": 1, "MARKET": 1}
    ).sort("merged_from_docs", -1).limit(5))

    return {
        "totalProducts": total_products,
        "uniqueBrands": unique_brands_count,
        "mergedProducts": merged_products_count,
        "avgConfidence": avg_conf,
        "brandDistribution": brand_dist,
        "mergeLevelDistribution": merge_dist,
        "confidenceDistribution": confidence_dist,
        "topMerged": top_merged
    }

@app.get("/dashboard/product/{merge_id}")
async def get_product_detail(merge_id: str):
    """Get single product detail from master_stock_data"""
    coll = get_collection(MASTER_STOCK_COL)
    
    # Try searching by merge_id first
    product = coll.find_one({"merge_id": merge_id}, {"_id": 0})
    
    if not product:
        # Fallback: Try searching by ObjectId as string
        try:
            from bson import ObjectId
            # Use string representation of ObjectId to find the document
            product = coll.find_one({"_id": ObjectId(merge_id)}, {"_id": 0})
        except Exception:
            product = None
            
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    return product

@app.get("/dashboard/low-confidence")
async def get_low_confidence(limit: int = 100):
    """Get low confidence products with limit"""
    coll = get_collection(MASTER_STOCK_COL)
    
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
async def export_master_stock(report_type: str = "all"):
    """Export MASTER_STOCK collection with filtering options"""
    print(f"📤 Starting export of {report_type} data...")
    coll = get_collection(MASTER_STOCK_COL)
    
    # Define Filter Queries
    query = {}
    if report_type == "merged":
        # QUERY: Items formed by merging 2 or more original documents
        query = {"$expr": {"$gt": [{"$size": "$merge_items"}, 1]}}
    elif report_type == "non_merged":
        # QUERY: Single items (merge_items size 1 OR field missing)
        query = {"$or": [
            {"merge_items": {"$exists": False}},
            {"merge_items": {"$size": 1}}
        ]}
    elif report_type == "low_confidence":
        query = {"llm_confidence_min": {"$lt": 0.8}}
        
    # Use find().batch_size to efficient memory management
    docs_cursor = coll.find(query, {"_id": 0})
    
    def generate_csv():
        import csv
        output = io.StringIO()
        writer = None
        
        # Define essential columns (ALL CAPS)
        essential_columns = [
            "UPC", "MERGE_ID", "SHEET_NAME", "BRAND", "FLAVOUR", "SIZE", 
            "NORMALIZED_ITEM", "ITEM", "MANUFACTURER", "PRODUCT_SEGMENT",
            "MARKETS", "MPACK", "FACTS", "DEC_23", "JAN_24", "FEB_24", "MAR_24",
            "APR_24", "MAY_24", "JUN_24", "JUL_24", "AUG_24", "SEP_24",
            "OCT_24", "NOV_24", "MAT_NOV_24",
            "MERGE_ITEMS", "MERGED_FROM_DOCS", "MERGE_LEVEL", "MERGE_RULE",
            "LLM_CONFIDENCE_MIN"
        ]
        
        count = 0
        try:
            for doc in docs_cursor:
                # Convert all keys to UPPERCASE
                doc_upper = {}
                for key, val in doc.items():
                    key_upper = key.upper().replace(" ", "_").replace("-", "_").replace("/", "_").replace("'", "")
                    
                    # Special formatting for merge_items - pipe separated without spaces
                    if key == "merge_items" and isinstance(val, list):
                        doc_upper[key_upper] = "|".join(map(str, val))
                    # Format other lists/dicts
                    elif isinstance(val, (list, dict)):
                        doc_upper[key_upper] = " | ".join(map(str, val)) if isinstance(val, list) else str(val)
                    else:
                        doc_upper[key_upper] = val
                
                # Initialize writer with headers on first row
                if writer is None:
                    # Use all keys from the first document as the schema
                    headers = [col for col in essential_columns if col in doc_upper]
                    other_cols = [col for col in doc_upper.keys() if col not in essential_columns]
                    headers.extend(other_cols)
                    
                    # extrasaction='ignore' is CRITICAL because MongoDB docs can have varying keys
                    writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
                    writer.writeheader()
                
                # Write row
                writer.writerow(doc_upper)

                
                # Yield data in chunks
                if count % 1000 == 0:
                    yield output.getvalue()
                    output.truncate(0)
                    output.seek(0)
                
                count += 1
                if count % 10000 == 0:
                    print(f"✅ Exported {count} rows...")
        except Exception as e:
            print(f"❌ Error during CSV generation at row {count}: {e}")
            # We can't change the status code now because headers are already sent
            # But we can yield an error message in the CSV itself
            output.write(f"\nERROR: Export interrupted. Error: {str(e)}\n")
            yield output.getvalue()
        
        # Final yield
        yield output.getvalue()
        print(f"🎉 Export complete. Total rows: {count}")

    headers = {
        'Content-Disposition': 'attachment; filename="master_stock_export.csv"'
    }
    return StreamingResponse(generate_csv(), headers=headers, media_type='text/csv')

@app.post("/database/reset")
async def reset_database(clear_cache: bool = False):
    """Clear all data collections. Optionally clears LLM cache as well."""
    from backend.database import reset_main_collections, clear_llm_cache
    
    try:
        reset_main_collections()
        if clear_cache:
            clear_llm_cache()
            
        return {
            "status": "success", 
            "message": "Database reset successful" + (" and cache cleared" if clear_cache else ""),
            "cache_cleared": clear_cache
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ─────────────────────────────────────────────────────
#  PIPELINE ENDPOINTS (New - UI Pipeline Support)
# ─────────────────────────────────────────────────────

@app.get("/export/flow1-report")
async def export_flow1_report():
    """Export single_stock_data (Flow 1 output) as CSV."""
    coll = get_collection(SINGLE_STOCK_COL)
    docs_cursor = coll.find({}, {"_id": 0})

    def generate():
        import csv
        output = io.StringIO()
        writer = None
        for doc in docs_cursor:
            doc_upper = {}
            for k, v in doc.items():
                key = k.upper().replace(" ", "_").replace("-", "_").replace("/", "_").replace("'", "")
                doc_upper[key] = " | ".join(map(str, v)) if isinstance(v, list) else str(v) if isinstance(v, dict) else v
            if writer is None:
                writer = csv.DictWriter(output, fieldnames=list(doc_upper.keys()), extrasaction='ignore')
                writer.writeheader()
            writer.writerow(doc_upper)
        yield output.getvalue()

    return StreamingResponse(
        generate(),
        headers={"Content-Disposition": 'attachment; filename="flow1_single_stock_export.csv"'},
        media_type="text/csv"
    )

@app.post("/pipeline/run-mapping")
async def pipeline_run_mapping():
    """Run Mapping Analysis (Flow 3). Wrapper around existing mapping_analysis.run_mapping() - no logic changes."""
    try:
        root = str(Path(__file__).parent.parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        from mapping_analysis import run_mapping, connect_db

        run_mapping()

        db, _, _, coll_results = connect_db()
        total = coll_results.count_documents({})
        l1 = coll_results.count_documents({"qa_fields.match_level": "LEVEL_1"})
        l2 = coll_results.count_documents({"qa_fields.match_level": "LEVEL_2"})
        gaps = coll_results.count_documents({"qa_fields.match_level": "GAP"})

        return {
            "status": "success",
            "total_mapped": total,
            "level1_matches": l1,
            "level2_matches": l2,
            "gaps": gaps,
            "message": f"Mapping complete. {total} records processed."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export/mapping-report")
async def export_mapping_report():
    """Export mapping_results collection as CSV (Flow 3 output)."""
    root = str(Path(__file__).parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    from mapping_analysis import connect_db

    db, _, _, coll_results = connect_db()
    data = list(coll_results.find({}, {"_id": 0}))

    def generate():
        import csv
        output = io.StringIO()
        writer = None
        for doc in data:
            flat = {k: v for k, v in doc.items() if k != "qa_fields"}
            if doc.get("qa_fields"):
                flat["match_level"] = doc["qa_fields"].get("match_level", "")
                flat["match_type"] = doc["qa_fields"].get("match_type", "")
            if writer is None:
                writer = csv.DictWriter(output, fieldnames=list(flat.keys()), extrasaction='ignore')
                writer.writeheader()
            writer.writerow(flat)
        yield output.getvalue()

    return StreamingResponse(
        generate(),
        headers={"Content-Disposition": 'attachment; filename="mapping_analysis_export.csv"'},
        media_type="text/csv"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  7-ELEVEN IMPORT — with LLM Cache on ArticleDescription
# ─────────────────────────────────────────────────────────────────────────────

SEVEN_ELEVEN_COL      = "7-eleven_data"
SEVEN_ELEVEN_CACHE_COL = "7-eleven_llm_cache"

# 7-Eleven prompt: extract exactly the 6 fields needed
_711_SYSTEM_PROMPT = """
You are a strict FMCG Data Scientist. Your task is to extract attributes from Malaysian 7-Eleven descriptions with 100% consistency.

Rules for Logic Stability:
1. ArticleDescription_clean: MUST remove all weights (e.g., 130g) and pack sizes (e.g., 10s, X10). Clean readable product name in Sentence-case.
2. 7E_Nrmsize: MUST be only the number + Unit (G/ML). For packs like 10Gx10, extract "10G".
3. 7E_MPack: If "X<n>", "<n>s", or "<n>x" exists, extract as "X<n>". Default "X1".
4. 7E_Variant: Extract sub-brands or product series (e.g., DAIRY MILK, MARIE, DUCHESS, CHUNKY, 4D). If it's a distinct sub-line, it is a Variant.
5. 7E_product_form: Extract the physical form (e.g., BISCUITS, CHIPS, GUMMY, CAKE, WAFER, STICK, CRACKER). If not clear or not applicable, "NONE".
6. 7E_flavour: Identify the primary taste or flavour profile (e.g., CHOCOLATE, ALMOND, MIXED NUT, FRUIT&NUT, BLACKFOREST, LEMON, STRAWBERRY, BBQ, SALTED, SEAWEED, SPICY, HOT & SPICY, CHEESE, KIMCHI, HONEY BUTTER, SALTED EGG, TIRAMISU). 
    - IMPORTANT: If it's a plain/standard version, ALWAYS use "ORIGINAL". Do not use "PLAIN" or "REGULAR".

Constraint: 
- Consistency is priority. 
- Return ONLY a valid JSON object. No conversational text.

Return format:
{
  "ArticleDescription_clean": "...",
  "7E_Nrmsize": "...",
  "7E_MPack": "X1",
  "7E_Variant": "NONE",
  "7E_product_form": "NONE",
  "7E_flavour": "NONE"
}

Examples:
- "Hwa Tai Lemon Treat 100g" -> {"ArticleDescription_clean": "Hwa Tai Lemon Treat", "7E_Nrmsize": "100G", "7E_MPack": "X1", "7E_Variant": "NONE", "7E_product_form": "NONE", "7E_flavour": "LEMON"}
- "Hwa Tai Luxury Cracker Vegetable 148g" -> {"ArticleDescription_clean": "Hwa Tai Luxury Cracker", "7E_Nrmsize": "148G", "7E_MPack": "X1", "7E_Variant": "NONE", "7E_product_form": "CRACKER", "7E_flavour": "VEGETABLE"}
- "ecoBrowns x KL Brice Seaweed 40g" -> {"ArticleDescription_clean": "ecoBrowns x KL Brice Seaweed", "7E_Nrmsize": "40G", "7E_MPack": "X1", "7E_Variant": "KL BRICE", "7E_product_form": "NONE", "7E_flavour": "SEAWEED"}
- "Kokiri Wow Seaweed Original 12g" -> {"ArticleDescription_clean": "Kokiri Wow Seaweed", "7E_Nrmsize": "12G", "7E_MPack": "X1", "7E_Variant": "NONE", "7E_product_form": "NONE", "7E_flavour": "SEAWEED/ORIGINAL"}
- "7-Eleven Potato Sticks Salted 50g" -> {"ArticleDescription_clean": "7-Eleven Potato Sticks Salted", "7E_Nrmsize": "50G", "7E_MPack": "X1", "7E_Variant": "NONE", "7E_product_form": "STICK", "7E_flavour": "SALTED"}
"""

def _call_711_llm(article_description: str) -> dict:
    """Call OpenAI with only the ArticleDescription; return 4 extra fields."""
    from backend.llm_client import flow2_client
    import json

    _fallback = {
        "ArticleDescription_clean": article_description,
        "7E_Nrmsize":     None,
        "7E_MPack":       "X1",
        "7E_Variant":     "NONE",
        "7E_product_form":"NONE",
        "7E_flavour":     "NONE",
    }
    user_msg = f'ARTICLE DESCRIPTION: "{article_description}"\n\nReturn JSON only.'
    try:
        raw = flow2_client.chat_completion(
            system_prompt=_711_SYSTEM_PROMPT,
            user_message=user_msg,
            temperature=0,
        ).strip()
    except Exception as e:
        print(f"  LLM call failed for '{article_description}': {e}")
        return _fallback

    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end + 1]
    try:
        data = json.loads(raw)
        for k, v in _fallback.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return _fallback


def _get_711_cache(article_description: str) -> dict | None:
    """Return cached LLM result for this ArticleDescription, or None."""
    coll = get_collection(SEVEN_ELEVEN_CACHE_COL)
    doc = coll.find_one({"article_description": article_description}, {"_id": 0, "result": 1})
    return doc["result"] if doc else None


def _save_711_cache(article_description: str, result: dict):
    """Upsert LLM result into 7-eleven_llm_cache."""
    coll = get_collection(SEVEN_ELEVEN_CACHE_COL)
    coll.update_one(
        {"article_description": article_description},
        {"$set": {
            "article_description": article_description,
            "result": result,
            "cached_at": datetime.utcnow().isoformat(),
        }},
        upsert=True,
    )


@app.post("/upload/7eleven")
async def upload_seven_eleven(file: UploadFile = File(...), request: Request = None):
    """
    Import a 7-Eleven Excel file into the 7-eleven_data collection.

    For each row:
      1. Check 7-eleven_llm_cache by ArticleDescription.
      2. If cache HIT  → use cached LLM result (no OpenAI call).
      3. If cache MISS → send ONLY ArticleDescription to OpenAI,
                         store result in cache, then save full row + enrichment.
    """
    print(f"\n📥 7-Eleven upload: {file.filename}")
    contents = await file.read()

    try:
        xl = pd.ExcelFile(io.BytesIO(contents))
        df = xl.parse(xl.sheet_names[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read Excel: {e}")

    # Normalise column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]

    if "ArticleDescription" not in df.columns:
        raise HTTPException(
            status_code=422,
            detail=f"Column 'ArticleDescription' not found. Columns present: {list(df.columns)}"
        )

    total        = len(df)
    cache_hits   = 0
    cache_misses = 0
    saved        = 0
    errors       = 0

    data_coll  = get_collection(SEVEN_ELEVEN_COL)
    
    # ✅ EXCLUSIVE IMPORT: Clear ALL old data from 7-eleven_data
    # This ensures mapping reports only contain items from the latest upload.
    # LLM Cache is NOT cleared, so it stays cost-efficient.
    print(f"🧹 Clearing existing data in {SEVEN_ELEVEN_COL}...")
    data_coll.delete_many({})

    has_code_col = "ArticleCode" in df.columns or "Article_Code" in df.columns
    code_col = "ArticleCode" if "ArticleCode" in df.columns else (
               "Article_Code" if "Article_Code" in df.columns else None)

    docs_to_upsert = []
    loop = asyncio.get_event_loop()
    # Use a shared executor or create one for this request
    executor = ThreadPoolExecutor(max_workers=10)

    for i, row in df.iterrows():
        # 🔗 CHECK DISCONNECTION: Stop if client cancelled
        # Yield to event loop to allow heartbeats/checks to run
        await asyncio.sleep(0)
        if request:
            if await request.is_disconnected():
                print(f"❌ Aborting 7-Eleven Import: Client disconnected at row {i}")
                executor.shutdown(wait=False)
                return {"status": "Stopped | Client disconnected", "rows_saved": saved}

        article_desc = str(row.get("ArticleDescription", "")).strip()
        if not article_desc or article_desc.lower() in ("nan", "none", ""):
            continue

        # ── 1. Cache check ──────────────────────────────────────────────
        cached = _get_711_cache(article_desc)
        if cached:
            llm_result = cached
            cache_hits += 1
        else:
            # ── 2. Call OpenAI (ArticleDescription only) ─────────────
            try:
                # Wrap sync LLM call in executor to avoid blocking the event loop
                llm_result = await loop.run_in_executor(executor, _call_711_llm, article_desc)
                _save_711_cache(article_desc, llm_result)
                cache_misses += 1
            except Exception as e:
                print(f"  ⚠️  LLM error for '{article_desc}': {e}")
                llm_result = {
                    "ArticleDescription_clean": article_desc,
                    "7E_Nrmsize":      None,
                    "7E_MPack":        "X1",
                    "7E_Variant":      "NONE",
                    "7E_product_form": "NONE",
                    "7E_flavour":      "NONE",
                }
                errors += 1

        # ── 3. Build document: original Excel cols + 4 LLM extra fields ───
        raw_row = {}
        for k, v in row.items():
            try:
                raw_row[k] = None if pd.isna(v) else v
            except (TypeError, ValueError):
                raw_row[k] = v
        doc = {
            **raw_row,
            # ── 6 LLM-enriched fields ───────────────────────────────────
            "ArticleDescription_clean": llm_result.get("ArticleDescription_clean", article_desc),
            "7E_Nrmsize":               llm_result.get("7E_Nrmsize"),
            "7E_MPack":                 llm_result.get("7E_MPack", "X1"),
            "7E_Variant":               llm_result.get("7E_Variant", "NONE"),
            "7E_product_form":          llm_result.get("7E_product_form", "NONE"),
            "7E_flavour":               llm_result.get("7E_flavour", "NONE"),
            # ── housekeeping ────────────────────────────────────────────
            "imported_at":              datetime.utcnow().isoformat(),
            "source_file":              file.filename,
        }
        docs_to_upsert.append(doc)
        saved += 1

    # ── 4. Bulk upsert / insert ──────────────────────────────────────────
    executor.shutdown(wait=False)
    if docs_to_upsert:
        if code_col:
            from pymongo import UpdateOne as PymUpdateOne
            ops = [
                PymUpdateOne(
                    {code_col: d.get(code_col)},
                    {"$set": d},
                    upsert=True,
                )
                for d in docs_to_upsert
            ]
            data_coll.bulk_write(ops, ordered=False)
        else:
            # Full collection was already cleared at start, so just insert
            data_coll.insert_many(docs_to_upsert)

    print(f"✅ 7-Eleven import done: {saved}/{total} rows | "
          f"cache hits={cache_hits} | new LLM calls={cache_misses} | errors={errors}")

    return {
        "status": "success",
        "filename": file.filename,
        "total_rows": total,
        "saved": saved,
        "cache_hits": cache_hits,
        "llm_calls_made": cache_misses,
        "errors": errors,
        "collection": SEVEN_ELEVEN_COL,
        "cache_collection": SEVEN_ELEVEN_CACHE_COL,
    }


@app.get("/cache/7eleven/stats")
async def get_711_cache_stats():
    """Return stats about the 7-Eleven LLM cache collection."""
    coll = get_collection(SEVEN_ELEVEN_CACHE_COL)
    total = coll.count_documents({})
    sample = list(coll.find({}, {"_id": 0, "article_description": 1, "result.name": 1,
                                  "result.brand": 1, "cached_at": 1}).limit(5))
    return {"total_cached": total, "sample": sample}


@app.delete("/cache/7eleven/clear")
async def clear_711_cache():
    """Clear the 7-Eleven LLM cache (forces re-enrichment on next import)."""
    coll = get_collection(SEVEN_ELEVEN_CACHE_COL)
    result = coll.delete_many({})
    return {"status": "success", "deleted": result.deleted_count}


from fastapi.staticfiles import StaticFiles



# Mount exports directory for Chatbot Excel downloads
export_dir = os.path.join(root_dir, "backend", "exports")
os.makedirs(export_dir, exist_ok=True)
app.mount("/exports", StaticFiles(directory=export_dir), name="exports")

@app.post("/api/qa/run-audit")
async def run_audit():
    """
    Triggers the AI Audit pipeline for all brands.
    """
    try:
        summary = audit_all_brands()
        return {"status": "success", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/qa/reports")
async def get_audit_reports():
    """
    Fetches all generated AI Audit reports.
    """
    report_dir = r"D:\Final_Input_and_Output\output_directry\AI_AUDIT_REPORTS"
    if not os.path.exists(report_dir):
        return []
    
    reports = []
    for file in os.listdir(report_dir):
        if file.endswith(".json"):
            with open(os.path.join(report_dir, file), 'r') as f:
                reports.append(json.load(f))
    return reports

@app.post("/api/qa/upload-audit")
async def upload_audit(file: UploadFile = File(...)):
    """
    Accepts a mapping CSV, runs AI Audit, and returns results + logs.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Identify brand from filename if possible
        brand_name = file.filename.replace('mapping_analysis_final_', '').replace('.csv', '')
        
        results, logs = process_audit_logic(df, brand_name)
        
        return {
            "status": "success",
            "brand": brand_name,
            "results": results,
            "logs": logs,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/mastering-audit")
async def mastering_audit(file: UploadFile = File(...)):
    """
    Accepts a Master Stock report, identifies missed groups among single items.
    """
    if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV or XLSX files are supported.")
    
    try:
        contents = await file.read()
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            df = pd.read_csv(io.BytesIO(contents))
        
        brand_name = file.filename.split('.')[0]
        results, logs = process_mastering_logic(df, brand_name)
        
        return {
            "status": "success",
            "brand": brand_name,
            "results": results,
            "logs": logs,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/stop-audit")
async def stop_audit(brand: str = Header(...)):
    """
    Sets the stop signal for a specific brand audit.
    """
    QA_STOP_SIGNALS[brand] = True
    MASTERING_STOP_SIGNALS[brand] = True
    return {"status": "success", "message": f"Stop signal sent for {brand}"}

class DiagnosticRequest(BaseModel):
    item_names: list[str]

@app.post("/api/qa/mastering-diagnostic")
async def mastering_diagnostic(req: DiagnosticRequest):
    """
    Returns a root-cause analysis for why a group of items didn't merge.
    """
    try:
        report = get_mastering_diagnostic(req.item_names)
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AuditDiagnosticRequest(BaseModel):
    gap_desc: str
    gap_size: float
    hero_candidates: list

@app.post("/api/qa/audit-diagnostic")
async def audit_diagnostic(req: AuditDiagnosticRequest):
    """
    Returns a root-cause analysis for an AI Audit mismatch.
    """
    try:
        report = get_audit_diagnostic(req.gap_desc, req.gap_size, req.hero_candidates)
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/translate-audit")
async def translate_audit(data: dict):
    """
    Translates an AI Audit diagnostic block to Tamil.
    """
    try:
        text = data.get("text")
        if not text:
            return {"translatedText": ""}
        translation = translate_audit_text(text)
        return {"status": "success", "translatedText": translation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/translate-text")
async def translate_text(data: dict):
    """
    Translates a block of text to Tamil using AI.
    """
    try:
        text = data.get("text")
        if not text:
            return {"translatedText": ""}
        translation = translate_diagnostic_text(text)
        return {"status": "success", "translatedText": translation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            port=8000,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            timeout_keep_alive=18000 # 5 hours for large file processing
        )
    else:
        # Local development without SSL
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            timeout_keep_alive=18000 # 5 hours for large file processing
        )
