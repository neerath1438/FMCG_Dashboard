# FMCG Dashboard: End-to-End Backend Technical Specification

This document provides a comprehensive technical breakdown of the FMCG Dashboard backend. It is designed to be a "Zero-Loss" guide for developers or AI models to understand, reproduce, or extend the system.

---

## 1. System Architecture
The system follows a microservice-style architecture with a **FastAPI** backend and **MongoDB** as the primary storage.

*   **Runtime**: Python 3.10+
*   **Database**: MongoDB (Atlas or Local)
*   **LLM Engine**: Azure Claude (Primary) with Azure OpenAI (Fallback for Mastering).
*   **Data Library**: Pandas (Batch Processing)

---

## 2. Database Schema (MongoDB)
The database `fmcg_mastering` contains the following core collections:

| Collection Name | Purpose | Key Fields |
| :--- | :--- | :--- |
| `raw_data` | Storage for every row from uploaded files (no processing). | Original file columns + `sheet_name`. |
| `single_stock_data` | Output of **Flow 1**. Normalized and grouped by UPC. | `UPC`, `ITEM`, summed monthly metrics, `merge_id`. |
| `master_stock_data` | Output of **Flow 2**. AI-mastered and clustered products. | `brand`, `flavour`, `size`, `merged_from_docs`, `merge_rule`. |
| `7-eleven_data` | Enriched 7-Eleven POS data. | `ArticleCode`, `GTIN`, `7E_Nrmsize`, `7E_MPack`, `7E_Variant`. |
| `LLM_CACHE_STORAGE` | Persistent cache for LLM extraction results. | `item` (key), `result` (JSON). |
| `7eleven_extra_items` | Results of the Gap Analysis. | `UPC`, `Article_Description`, `Match_Level`, `Main_UPC`. |

---

## 3. Data Processing Pipeline

### Stage 1: Flow 1 (Ingestion & Data Normalization)
**File**: `backend/processor.py` -> `process_nielsen_dataframe`

1.  **Column Identification**: Automatically maps columns like `UPC`, `MARKETS`, `MPACK`, `FACTS`.
2.  **Deterministic Sorting**: Sorts data by `UPC`, `MARKET`, and `FACTS` to ensure consistent grouping.
3.  **UPC-Based Grouping**:
    *   Groups rows by `UPC + MARKETS + MPACK + FACTS`. 
    *   **Rule**: Same UPC with different `MPACK` (e.g., X1 vs X12) are kept separate.
4.  **Metric Aggregation**: Sums all monthly columns (e.g., `MAT NOV'24`, `JAN'24`) for rows in the same group.
5.  **Metadata Generation**: Assigns a unique `merge_id` and tracks `merged_from_docs`.

### Stage 2: Flow 2 (AI Mastering & Clustering)
**File**: `backend/processor.py` -> `process_llm_mastering_flow_2`

This stage uses AI to "Master" the products by clustering similar variants together.

1.  **Attribute Extraction (LLM)**:
    *   Calls `normalize_item_llm` for each unique item.
    *   **Prompt Strategy**: High-precision few-shot prompting to extract `Brand`, `Product Line`, `Flavour`, `Size`, `Variant`, and `Product Form`.
    *   **Strict Size Extraction**: AI is forbidden from calculating weights (e.g., "15g X 12" must stay "15g X 12").
2.  **Hierarchical Grouping**:
    *   **High Confidence (>= 0.92)**: Groups items by `Brand + Product Line + Form + Flavour + MPack + Market`.
    *   **Low Confidence**: Groups by `Brand + Simple Clean Signature` to avoid false merges.
3.  **Fuzzy Merge Stage**:
    *   Residual items are checked for string similarity using `SequenceMatcher`.
    *   Similarity > 0.85 (after synonym normalization) triggers a merge.
4.  **Hard Guards (The Audit)**:
    *   **Family Guard**: Ensures different product lines (e.g., "POCKY" vs "PRETZ") never merge.
    *   **Flavour Guard**: Prevents merging conflicting flavours (e.g., "HAZELNUT" vs "STRAWBERRY").
5.  **Master Record Selection**:
    *   The "Master" item name is chosen from the record with the highest **MAT Sales Value**.

---

## 4. Competitive Gap Analysis Logic
**File**: `gap_analysis_7eleven.py`

Matches Nielsen Market data (Master Stock) against 7-Eleven data.

*   **Data Preparation**: Normalizes sizes (e.g., "300G", "0.3KG") to numeric values (grams/ml).
*   **Matching Levels**:
    1.  **L1 Match (UPC Match)**: If `Nielsen.UPC == 7Eleven.GTIN`.
    2.  **L2 Match (Attribute Match)**: If `Brand`, `Variant`, `MPack`, and `Size (±5g tolerance)` match.
*   **Output**: High-performing items in the market marked as "NOT CARRIED" represent immediate sales opportunities.

---

## 5. LLM Engineering & Redundancy
**File**: `backend/llm_client.py`

*   **Clients**:
    *   `llm_client`: Uses Azure Claude with Azure OpenAI as an automatic fallback (for Chatbot).
    *   `flow2_client`: Optimized for bulk processing (OpenAI only, faster, concurrent).
*   **Rate Limiting**: Intelligent retry logic using `Retry-After` headers and exponential backoff.
*   **Caching**: Dual-layer (Memory + MongoDB) to minimize API cost and latency.

---

## 6. API & Integration
**File**: `backend/main.py`

*   `/upload/excel`: Triggers Flow 1.
*   `/process/llm-mastering/{sheet}`: Triggers Flow 2.
*   `/api/audit/counts`: Provides the "Data Funnel" stats (Raw -> Single -> Master -> Gaps).
*   `/chatbot/query`: Natural language interface for product queries.

---

## 7. Key Code Utilities
*   `normalize_synonyms()`: Regex-based term normalization (e.g., "CHOC" -> "CHOCOLATE").
*   `simple_clean_item()`: Strips noise and sorts keywords to create a robust string signature.
*   `extract_size_val()`: Numeric weight extraction for tolerance matching.

---

> [!IMPORTANT]
> This backend is built for **Precision over Speed**. Every merge is audited by "Hard Guards" to ensure that the data provided to 7-Eleven for business decisions is 100% accurate.

---

## 8. Final Target Strategy 🎯

The ultimate goal of this backend system is not just data cleaning, but driving measurable business growth for 7-Eleven through data-driven insights.

### Strategic Objectives:
1.  **MPack Conversion**: Identify items where the general market prefers bulk packaging (e.g., `X12`, `X24`) while 7-Eleven only stocks single units (`X1`). Converting these to multi-packs is the fastest way to increase basket value.
2.  **Assortment Optimization**: Detect "Market Heroes"—products that are top-sellers in Pen Malaysia but are entirely missing from 7-Eleven's current inventory.
3.  **Pricing Benchmark**: Compare 7-Eleven's price-per-unit against the market's bulk-buy rates to ensure competitiveness.
4.  **Autonomous Operations**: Achieve 99%+ accuracy in product mastering with zero human intervention, allowing the category management team to focus on sales rather than data entry.

---

> [!IMPORTANT]
> This system transforms 7-Eleven from a traditional retailer into a data-driven powerhouse, capable of responding to market trends in real-time.
