import pandas as pd
import os
import glob

# Set the path to the folder containing the CSV files
folder_path = 'Bayut-scrape-files'  # 🔁 Change this

# Get all CSV file paths in the folder
csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# Read and combine all CSVs
combined_df = pd.concat([pd.read_csv(file) for file in csv_files], ignore_index=True)

# Save to a new CSV file
combined_df.to_csv('bayut_combined_output_105pages.csv', index=False)

print(f"✅ Combined {len(csv_files)} files into 'combined_output.csv'")
