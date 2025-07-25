import pandas as pd
import os
import glob

# Change this to your actual folder path
folder_path = 'Bayut-scrape-files'

# Find all .xlsx files in the folder
xlsx_files = glob.glob(os.path.join(folder_path, '*.xlsx'))

if not xlsx_files:
    print("❌ No Excel files found in the specified folder!")
else:
    # Read and combine all Excel files
    combined_df = pd.concat([pd.read_excel(file) for file in xlsx_files], ignore_index=True)
    
    # Save to a new Excel file (or CSV if you prefer)
    combined_df.to_excel('bayut_combined_output_105pages.xlsx', index=False)
    print(f"✅ Combined {len(xlsx_files)} files into 'combined_output.xlsx'")
