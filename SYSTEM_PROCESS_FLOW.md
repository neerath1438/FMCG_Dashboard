# FMCG Dashboard: End-to-End System Process Flow

This document provides a step-by-step breakdown of how the FMCG Dashboard processes data, from raw Excel uploads to AI-powered merging and final competitive gap analysis.

---

## 1. Phase 1: Raw Data Ingestion & Initial Cleaning (Flow 1)
**Objective**: To take messy, raw Excel/CSV files and organize them into standardized, traceable records.

*   **Step 1.1: File Upload & Format Detection**: The system accepts `.xlsx`, `.xls`, or `.csv` files. It automatically identifies sheets and determines if the file is a "Nielsen Market Report" or "7-Eleven POS Data."
*   **Step 1.2: Column Mapping**: It dynamically maps various column naming conventions (e.g., finding "UPC", "EAN", or "GTIN") to bridge the gap between different data providers.
*   **Step 1.3: Raw Data Logging**: Every single row from the original file is saved "as-is" into the `raw_data` collection in MongoDB for audit purposes.
*   **Step 1.4: Strict Grouping & Aggregation**: 
    *   Data is grouped by **UPC + Market + MPACK + Facts**.
    *   Monthly metrics (Sales Value, Units) are summed for all rows matching these criteria.
    *   Example: If the same UPC appears twice in the same market but for different months, they are merged into one record with accumulated values.
*   **Step 1.5: Result Persistence**: The clean, grouped data is saved to `single_stock_data`.

---

## 2. Phase 2: AI-Powered Product Mastering (Flow 2)
**Objective**: To resolve "Dirty Data" (typos, different naming styles) using Artificial Intelligence and cluster similar products together.

*   **Step 2.1: Attribute Extraction (LLM)**:
    *   The system sends raw item descriptions (e.g., `OAT KRUNCH CHOCO 156G X 12`) to a Large Language Model (Azure Claude/GPT).
    *   The AI extracts: **Brand** (Munchys), **Product Line** (Oat Krunch), **Flavour** (Chocolate), **Size** (156G), and **Pack Type** (X12).
*   **Step 2.2: Intelligent Clustering**:
    *   Instead of matching by exact name, the system matches by these AI-extracted attributes.
    *   Products with the same Brand, Flavour, and Size are clustered into a single "Master Record."
*   **Step 2.3: Fuzzy Matching Fallback**: If the AI is unsure (confidence < 92%), the system uses a high-speed fuzzy algorithm (Levenshtein) to detect spelling mistakes (e.g., `CADBURY` vs `CDBRY`).
*   **Step 2.4: Hard Guard Audit (The Safety Net)**:
    *   A automated "Guard" checks the merge. It ensures that different flavours (e.g., `STRAWBERRY` vs `CHOCOLATE`) or different product families NEVER merge, even if the names look similar.
*   **Step 2.5: MAT Leader Selection**: Within a cluster, the record with the highest annual sales (MAT - Moving Annual Total) is crowned the "Master Record" and its name is used for the entire group.
*   **Step 2.6: Final Storage**: Mastered items are saved to `master_stock_data`.

---

## 3. Phase 3: Competitive Gap Analysis (Mapping)
**Objective**: To compare what is selling in the general market (Nielsen) against what 7-Eleven is currently carrying.

*   **Step 3.1: Data Normalization**: 7-Eleven data and Nielsen Master Stock are normalized (Uppercase, removed punctuation, conversion of weights like `300gm` to `300.0`).
*   **Step 3.2: Level 1 - Exact UPC Match**: The system first looks for an exact match where `7E_GTIN == Nielsen_UPC`.
*   **Step 3.3: Level 2 - Attribute & Flavour Match**: 
    *   If no UPC match is found, the system searches by **Normalized Brand + Variant + MPack + Size**.
    *   **Tolerance**: It allows a ±5g weight difference to handle rounding errors between datasets.
*   **Step 3.4: Synonym Handling**: The system uses a dictionary to bridge naming gaps (e.g., knowing that `ORIGINAL`, `PLAIN`, and `REGULAR` all mean the same thing).
*   **Step 3.5: Bi-Directional Gap Identification**:
    *   **7-Eleven Gaps**: Items 7-Eleven carries that don't have a market equivalent.
    *   **Market Heroes (Master Gaps)**: Top-selling items in the general market that are **missing** from 7-Eleven's data. These are the primary targets for assortment expansion.

---

## 4. Phase 4: Reporting & Coverage Insights
**Objective**: To turn data into actionable sales strategies and measure market presence.

*   **Step 4.1: Item Coverage**: Calculates what % of 7-Eleven's current library is successfully mapped to market data.
*   **Step 4.2: Market Value Coverage (Value Share)**: The most critical metric. It measures what % of the Total Market Sales Value (MAT) is captured by 7-Eleven's current product range.
*   **Step 4.3: Opportunity Priority**: Market Heroes are ranked by their sales value. This tells 7-Eleven exactly which products will give them the biggest boost if they "fill the gap."
*   **Step 4.4: Unified Excel Export**: A consolidated report combining 7-Eleven data and Market gaps in one view.

---

## 5. Appendix: QA Verification Queries
Use these MongoDB queries in **NoSQLBooster** to verify the improvements during client meetings.

### Q1: Overall Mapping Summary
Shows the breakdown of Matches vs Gaps.
```javascript
db.mapping_results.aggregate([
  { $group: { _id: "$Match_Level", count: { $sum: 1 } } },
  { $project: { "Status": "$_id", "Count": "$count", "Percentage": { $round: [{ $multiply: [{ $divide: ["$count", 3220] }, 100] }, 2] } } }
])
```

### Q2: Unique ArticleCode Coverage
Verifies that the "Missing ArticleCodes" issue is resolved.
```javascript
db.mapping_results.distinct("ArticleCode", { "Match_Level": { $in: ["LEVEL_1", "LEVEL_2"] } }).length
```

### Q3: Proof of Flexible UPC Matching (Suffix Matching)
Shows items that were matched despite different GTIN/UPC lengths (the 8-digit fix).
```javascript
db.mapping_results.find({ 
  "Match_Type": "Exact/Flexible UPC Match", 
  $expr: { $ne: [ { $strLenCP: "$GTIN" }, { $strLenCP: { $ifNull: ["$Main_UPC", ""] } } ] } 
}).limit(10)
```

### Q4: Top Market Heroes (Gaps to Fill)
Identifies the highest value opportunities for 7-Eleven.
```javascript
db.mapping_results.find({ "Match_Level": "MARKET_HERO" })
  .sort({ "Matched_MAT": -1 })
  .limit(20)
```

---

## 5. Technical Summary (Tamil - தமிழ் தொகுப்பு)

1.  **Flow 1 (தரவு சேகரிப்பு)**: எக்செல் (Excel) கோப்புகளைப் பெற்று, அவற்றில் உள்ள UPC குறியீடுகளை வைத்து தரவுகளை வகைப்படுத்தி கிளீன் செய்கிறது.
2.  **Flow 2 (AI மாஸ்டரிங்)**: செயற்கை நுண்ணறிவு (AI) மூலம் தயாரிப்புப் பெயர்களில் உள்ள பிழைகளைத் திருத்தி, பிராண்ட் மற்றும் சுவையை (Brand & Flavour) சரியாகப் பிரிக்கிறது.
3.  **Gap Analysis (ஒப்பீடு)**: சந்தையில் (Nielsen) அதிகம் விற்பனையாகும் பொருட்கள் 7-Eleven கடைகளில் உள்ளனவா என்று ஒப்பிட்டுப் பார்க்கிறது.
4.  **Sales Opportunity**: 7-Eleven கடைகளில் இல்லாத, ஆனால் வெளியூரில் அதிகம் விற்கும் "Market Heroes" தயாரிப்புகளை இது கண்டறிந்து சொல்கிறது.

