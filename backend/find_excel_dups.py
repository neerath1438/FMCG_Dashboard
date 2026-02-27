import pandas as pd
import os

def identify_duplicates():
    file_path = r'd:\git\FMCG_Dashboard\backend\Wersel_7E_Data.xlsx'
    df = pd.read_excel(file_path)
    
    # Identify rows where ArticleDescription is duplicated
    # We'll look for cases where ArticleDescription is same but ArticleCode might be different
    duplicates = df[df.duplicated(subset=['ArticleDescription'], keep=False)].sort_values(by='ArticleDescription')
    
    print(f"Total rows involved in duplication: {len(duplicates)}")
    if not duplicates.empty:
        print("\nDuplicate items found in Excel:")
        # Show first few columns to see if ArticleCode is different
        print(duplicates[['ArticleDescription', 'ArticleCode']].head(10))
        
        # Check if they are EXACT row duplicates
        exact_dups = df[df.duplicated(keep=False)]
        print(f"\nExact row duplicates: {len(exact_dups)}")

if __name__ == "__main__":
    identify_duplicates()
