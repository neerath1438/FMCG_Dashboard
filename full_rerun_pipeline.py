import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = os.getcwd()
if root_dir not in sys.path:
    sys.path.append(root_dir)

from backend.processor import process_llm_mastering_flow_2
from gap_analysis_7eleven import run_gap_analysis
from export_final_reports import export_reports

async def main():
    print("🚀 Starting FULL RE-RUN of the FMCG Pipeline...")
    
    # 0. Phase 0: Reprocess Flow 1 (Raw -> Single Stock)
    print("\n--- Phase 0: Flow 1 Reprocessing (Raw -> Single) ---")
    try:
        from backend.processor import reprocess_flow_1_from_db
        await reprocess_flow_1_from_db()
        print("✅ Phase 0 Complete.")
    except Exception as e:
        print(f"❌ Error during Phase 0: {e}")
        return

    # 1. Flow 2 Mastering (Calculates Main_UPC based on highest stock)
    print("\n--- Phase 1: LLM Mastering (Flow 2) ---")
    try:
        # sheet_name is usually "wersel_match" or the name of the sheet in single_stock_data
        await process_llm_mastering_flow_2("wersel_match")
        print("✅ Flow 2 Mastering Complete.")
    except Exception as e:
        print(f"❌ Error during Flow 2 Mastering: {e}")
        return

    # 2. Gap Analysis (Uses the Main_UPC calculated or defined)
    print("\n--- Phase 2: 7-Eleven Gap Analysis ---")
    try:
        run_gap_analysis()
        print("✅ Gap Analysis Complete.")
    except Exception as e:
        print(f"❌ Error during Gap Analysis: {e}")
        return

    # 3. Export Final Reports
    print("\n--- Phase 3: Exporting Final Reports ---")
    try:
        export_reports()
        print("✅ Export of 6 reports complete.")
    except Exception as e:
        print(f"❌ Error during Export: {e}")
        return

    print("\n🎉 ALL PHASES COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    asyncio.run(main())
