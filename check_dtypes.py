import pandas as pd
import numpy as np

file_path = "ten_brand_stock.xlsx"

try:
    df = pd.read_excel(file_path)
    print("Columns and Types:")
    print(df.dtypes)
    
    monthly_cols = [c for c in df.columns if any(m in str(c).upper() for m in 
            ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "W/E", "MAT"])]
    
    print("\nMonthly Cols Sample:")
    print(df[monthly_cols].head(5))
    
    for col in monthly_cols:
        non_numeric = df[pd.to_numeric(df[col], errors='coerce').isna()][col]
        if not non_numeric.empty:
            print(f"\nPotential non-numeric values in {col}:")
            print(non_numeric.unique()[:5])

except Exception as e:
    print(f"Error: {e}")
