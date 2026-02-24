from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI(title="FMCG Dashboard API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["fmcg_mastering"]

# Pydantic Models
class DashboardStats(BaseModel):
    input_rows: int
    items_merged: int
    reduction_percentage: float
    output_rows: int
    unique_upcs: int
    merged: int
    single: int
    unique_brands: int
    items_need_review: int
    status: str

class AuditCounts(BaseModel):
    raw_nielsen: int
    single_stock: int
    master_stock: int
    ai_enriched: int
    carried: int
    gaps: int
    seven_eleven_unique: int

# API Endpoints

@app.get("/")
async def root():
    return {"message": "FMCG Dashboard API", "status": "running"}

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get main dashboard statistics"""
    try:
        # Query all collections for live counts
        nielsen_query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
        
        raw_nielsen = db["nielsen_data"].count_documents({"Facts": "Sales Value"})
        single_stock = db["single_stock_data"].count_documents({})
        master_stock = db["master_stock_data"].count_documents(nielsen_query)
        
        # Count merged items (documents with merged_from_docs > 1)
        merged_pipeline = [
            {"$match": nielsen_query},
            {"$match": {"merged_from_docs": {"$exists": True, "$gt": 1}}}
        ]
        items_merged = len(list(db["master_stock_data"].aggregate(merged_pipeline)))
        
        # Calculate reduction percentage
        reduction_pct = round(((raw_nielsen - master_stock) / raw_nielsen * 100), 1) if raw_nielsen > 0 else 0
        
        # Count unique UPCs
        unique_upcs = len(db["master_stock_data"].distinct("UPC", nielsen_query))
        
        # Count unique brands
        unique_brands = len(db["master_stock_data"].distinct("UPC_GroupName", nielsen_query))
        
        # Items needing review (example: records with missing attributes)
        items_need_review = db["master_stock_data"].count_documents({
            **nielsen_query,
            "$or": [
                {"UPC_GroupName": {"$in": ["NONE", "UNKNOWN", None]}},
                {"NRMSIZE": {"$in": ["NONE", None]}}
            ]
        })
        
        return DashboardStats(
            input_rows=raw_nielsen,
            items_merged=items_merged,
            reduction_percentage=reduction_pct,
            output_rows=master_stock,
            unique_upcs=unique_upcs,
            merged=master_stock,
            single=single_stock - master_stock if single_stock > master_stock else 0,
            unique_brands=unique_brands,
            items_need_review=items_need_review,
            status="Current Status"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audit/counts", response_model=AuditCounts)
async def get_audit_counts():
    """Get audit dashboard counts"""
    try:
        nielsen_query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
        
        raw_nielsen = db["nielsen_data"].count_documents({"Facts": "Sales Value"})
        single_stock = db["single_stock_data"].count_documents({})
        master_stock = db["master_stock_data"].count_documents(nielsen_query)
        ai_enriched = db["seven_eleven_data"].count_documents({})
        carried = db["nielsen_carried_items"].count_documents({})
        gaps = db["nielsen_gap_items"].count_documents({})
        seven_eleven_unique = db["seven_eleven_extra_items"].count_documents({})
        
        return AuditCounts(
            raw_nielsen=raw_nielsen,
            single_stock=single_stock,
            master_stock=master_stock,
            ai_enriched=ai_enriched,
            carried=carried,
            gaps=gaps,
            seven_eleven_unique=seven_eleven_unique
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/merge/details")
async def get_merge_details(limit: int = 413):
    """Get merge details for Master Stock modal"""
    try:
        nielsen_query = {"Facts": "Sales Value", "Markets": "Pen Malaysia"}
        
        # Find documents with merged_from_docs
        pipeline = [
            {"$match": {**nielsen_query, "merged_from_docs": {"$exists": True, "$gt": 1}}},
            {"$limit": limit},
            {"$project": {
                "_id": 0,
                "master_id": "$_id",
                "main_upc": "$UPC",
                "brand": "$UPC_GroupName",
                "item": "$ITEM",
                "size": "$NRMSIZE",
                "merged_count": "$merged_from_docs",
                "merged_items": "$merged_items"
            }}
        ]
        
        merges = list(db["master_stock_data"].aggregate(pipeline))
        return {"count": len(merges), "merges": merges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filtered/records")
async def get_filtered_records(limit: int = 7):
    """Get filtered records for Single Stock modal"""
    try:
        # Find duplicate records that were filtered
        pipeline = [
            {"$group": {
                "_id": {"UPC": "$UPC", "ITEM": "$ITEM"},
                "count": {"$sum": 1},
                "docs": {"$push": "$$ROOT"}
            }},
            {"$match": {"count": {"$gt": 1}}},
            {"$limit": limit}
        ]
        
        duplicates = list(db["nielsen_data"].aggregate(pipeline))
        
        filtered = []
        for dup in duplicates:
            filtered.append({
                "upc": dup["_id"]["UPC"],
                "item": dup["_id"]["ITEM"],
                "duplicate_count": dup["count"],
                "records": dup["docs"][:2]  # Show first 2 duplicates
            })
        
        return {"count": len(filtered), "filtered": filtered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gap/analysis")
async def get_gap_analysis():
    """Get gap analysis summary"""
    try:
        carried = db["nielsen_carried_items"].count_documents({})
        gaps = db["nielsen_gap_items"].count_documents({})
        seven_eleven_unique = db["seven_eleven_extra_items"].count_documents({})
        
        # Sample gap items
        gap_samples = list(db["nielsen_gap_items"].find({}, {
            "_id": 0,
            "UPC": 1,
            "ITEM": 1,
            "UPC_GroupName": 1,
            "NRMSIZE": 1
        }).limit(10))
        
        return {
            "carried": carried,
            "gaps": gaps,
            "seven_eleven_unique": seven_eleven_unique,
            "gap_samples": gap_samples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
