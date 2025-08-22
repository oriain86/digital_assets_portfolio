import pandas as pd
import numpy as np


def analyze_portfolio_file(file_path):
    """Analyze portfolio file for potential issues."""
    
    # Read the file
    df = pd.read_csv(file_path, dtype=str)
    
    print(f"=== File Analysis: {file_path} ===")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}\n")
    
    # Check for missing values
    print("1. MISSING VALUES:")
    missing = df.isnull().sum()
    for col, count in missing.items():
        if count > 0:
            print(f"   {col}: {count} missing values")
    
    # Check numeric columns
    print("\n2. NUMERIC COLUMNS ANALYSIS:")
    numeric_cols = ['amount', 'price_usd', 'total_usd', 'fee_usd']
    
    for col in numeric_cols:
        if col in df.columns:
            print(f"\n   {col}:")
            
            # Check for dollar signs
            if df[col].notna().any():
                has_dollar = df[col].fillna('').str.contains('\\$').sum()
                if has_dollar > 0:
                    print(f"   - {has_dollar} values contain $ symbol")
    
    # Transaction types
    print("\n3. TRANSACTION TYPES:")
    type_counts = df['type'].value_counts()
    for t, count in type_counts.items():
        print(f"   {t}: {count}")
    
    return df


# Example usage:
# df = analyze_portfolio_file('path/to/your/transactions.csv')
