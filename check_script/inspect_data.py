import pandas as pd
import os

file_path = "ten_brand_stock.xlsx"

try:
    df = pd.read_excel(file_path)
    print("Columns:")
    print(df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head().to_markdown())
    print("\nData Types:")
    print(df.dtypes)
    
    # Check for specific columns mentioned in feedback
    interesting_cols = [col for col in df.columns if any(x in col.upper() for x in ['MARKET', 'MPACK', 'SIZE', 'FACT', 'UPC', 'ITEM'])]
    print("\nInteresting Columns found:", interesting_cols)
    
except Exception as e:
    print(f"Error reading file: {e}")
