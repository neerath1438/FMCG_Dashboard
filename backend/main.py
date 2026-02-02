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
from pydantic import BaseModel
import io
import pandas as pd
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Optional

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
    coll = get_collection(MASTER_STOCK_COL)
    product = coll.find_one({"merge_id": merge_id}, {"_id": 0})
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
