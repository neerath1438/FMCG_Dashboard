import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

def export_merging_breakdown():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = "fmcg_mastering"
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # 1. Fetch Master Records with their merged UPCs
    print("Fetching master stock data...")
    master_docs = list(db["master_stock_data"].find({}, {
        "merge_id": 1, 
        "ITEM": 1, 
        "merged_upcs": 1, 
        "merge_rule": 1, 
        "merge_level": 1,
        "BRAND": 1,
        "variant": 1,
        "flavour": 1,
        "size": 1
    }))
    
    if not master_docs:
        print("No master data found.")
        return

    # 2. Flatten/Explode the merged_upcs
    flattened_data = []
    
    # We want to map EACH UPC to its Master Cluster Metadata
    for doc in sorted(master_docs, key=lambda x: x.get('merge_id', '')):
        master_info = {
            "MASTER_MERGE_ID": doc.get("merge_id"),
            "MASTER_ITEM_NAME": doc.get("ITEM"),
            "MASTER_BRAND": doc.get("BRAND"),
            "MASTER_VARIANT": doc.get("variant"),
            "MASTER_FLAVOUR": doc.get("flavour"),
            "MASTER_SIZE": doc.get("size"),
            "MERGE_RULE": doc.get("merge_rule"),
            "MERGE_LEVEL": doc.get("merge_level")
        }
        
        upcs = doc.get("merged_upcs", [])
        if not upcs:
            # Fallback if merged_upcs is missing (should not happen in current pipeline)
            upc_main = doc.get("UPC")
            if upc_main:
                upcs = [upc_main]
            
        for upc in upcs:
            if upc:
                row = master_info.copy()
                row["JOIN_UPC"] = str(upc)
                flattened_data.append(row)

    df_map = pd.DataFrame(flattened_data)
    
    # 3. Fetch Gap Analysis Results (L1/L2 Matches)
    print("Fetching 7-Eleven gap analysis results...")
    gap_docs = list(db["7eleven_extra_items"].find({}, {"UPC": 1, "Match_Level": 1, "ArticleCode": 1}))
    df_gap = pd.DataFrame(gap_docs)
    if not df_gap.empty:
        df_gap["UPC"] = df_gap["UPC"].astype(str)
        # Unique mapping for UPC -> Match Status
        df_gap = df_gap.drop_duplicates(subset=["UPC"])
    
    # 4. Fetch Raw Data to get Original Item Names
    print("Fetching raw Nielsen data for original names...")
    raw_docs = list(db["raw_data"].find({}, {"UPC": 1, "ITEM": 1, "BRAND": 1, "VARIANT": 1, "FACTS": 1}))
    df_raw = pd.DataFrame(raw_docs)
    df_raw["UPC"] = df_raw["UPC"].astype(str)
    
    # 5. Merge/Join
    print(f"Joining {len(df_raw)} original records with master mapping...")
    # Join Raw with Master Map
    df_final = pd.merge(
        df_raw, 
        df_map, 
        left_on="UPC", 
        right_on="JOIN_UPC", 
        how="left"
    )
    
    # Then Join with Gap Analysis (for L1/L2 info)
    if not df_gap.empty:
        df_final = pd.merge(
            df_final,
            df_gap[["UPC", "Match_Level", "ArticleCode"]],
            on="UPC",
            how="left",
            suffixes=('', '_7E')
        )
    
    # Rename for clarity
    df_final = df_final.rename(columns={
        "Match_Level_7E": "7E_GAP_MATCH_LEVEL",
        "ArticleCode_7E": "7E_ARTICLE_CODE"
    })
    
    # Drop redundant columns
    if "JOIN_UPC" in df_final.columns:
        df_final = df_final.drop(columns=["JOIN_UPC"])
        
    # Standardize column naming for clarity
    df_final = df_final.rename(columns={
        "ITEM": "RAW_ITEM_NAME",
        "BRAND": "RAW_BRAND",
        "VARIANT": "RAW_VARIANT",
        "FACTS": "RAW_FACTS"
    })

    # Order columns logically
    cols_order = [
        "UPC", "RAW_ITEM_NAME", "RAW_BRAND", "RAW_VARIANT", "RAW_FACTS",
        "MASTER_MERGE_ID", "MASTER_ITEM_NAME", "MASTER_BRAND", "MASTER_VARIANT", 
        "MASTER_FLAVOUR", "MASTER_SIZE", "MERGE_RULE", "MERGE_LEVEL",
        "Match_Level", "7E_ARTICLE_CODE" # Adding Article code and Match Level
    ]
    
    # Re-map Match_Level to a more descriptive name if needed
    if "Match_Level" in df_final.columns:
        df_final = df_final.rename(columns={"Match_Level": "7E_MATCH_TYPE"})

    # Clean up empty values
    df_final = df_final.fillna("NONE")
    
    # Final column list pruning
    cols_to_show = [
        "UPC", "RAW_ITEM_NAME", "RAW_BRAND", "RAW_VARIANT", "RAW_FACTS",
        "MASTER_MERGE_ID", "MASTER_ITEM_NAME", "MASTER_BRAND", "MASTER_VARIANT", 
        "MASTER_FLAVOUR", "MASTER_SIZE", "MERGE_RULE", "MERGE_LEVEL",
        "7E_MATCH_TYPE", "7E_ARTICLE_CODE"
    ]
    df_final = df_final[[c for c in cols_to_show if c in df_final.columns]]

    # 6. Export
    target_dir = r"D:\master_final_data"
    output_path = os.path.join(target_dir, "Nielsen_Merging_Full_Breakdown_v3.xlsx")
    
    print(f"Exporting {len(df_final)} records to {output_path}...")
    df_final.to_excel(output_path, index=False)
    print("✅ Export complete!")

    client.close()

if __name__ == "__main__":
    export_merging_breakdown()
