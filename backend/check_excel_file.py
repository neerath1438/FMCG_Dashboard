import pandas as pd
import os

def check_excel():
    file_path = r'd:\git\FMCG_Dashboard\backend\Wersel_7E_Data.xlsx'
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    df = pd.read_excel(file_path)
    print(f"Total Rows in Excel: {len(df)}")
    print(f"Unique ArticleDescriptions: {df['ArticleDescription'].nunique()}")
    print(f"Unique ArticleCodes: {df['ArticleCode'].nunique()}")
    
    # Check for duplicates ArticleDescriptions in the file itself
    dups = df[df.duplicated(subset=['ArticleDescription'], keep=False)]
    if not dups.empty:
        print(f"Found {len(dups)} rows with duplicate ArticleDescriptions in the file.")

if __name__ == "__main__":
    check_excel()
