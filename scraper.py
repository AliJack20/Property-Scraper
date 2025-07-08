import pandas as pd
from datetime import datetime
import os

# ------------------------------
# 1) Load input Excel
# ------------------------------
df = pd.read_excel("properties.xlsx")
properties = df.to_dict(orient="records")

print(f"✅ Loaded {len(properties)} properties")

# ------------------------------
# 2) Dummy scrape logic
# ------------------------------
results = []

for prop in properties:
    snapshot = {
        "property_id": prop['Property_ID'],
        "platform": prop['Platform'],
        "listing_url": prop['Listing_URL'],
        "area": prop['Area'],
        "unit_type": prop['Unit_Type'],
        "date_scraped": datetime.today().strftime('%Y-%m-%d'),
        "reviews": 123,   # fake
        "rating": 4.8,    # fake
        "price_today": 100, # fake
        "is_available_today": True,  # fake
        "amenities": "Wifi, Kitchen"
    }
    results.append(snapshot)

# ------------------------------
# 3) Save to daily Excel file
# ------------------------------
output_df = pd.DataFrame(results)

# Make sure output folder exists
os.makedirs("output", exist_ok=True)

today = datetime.today().strftime('%Y-%m-%d')
output_filename = f"output/{today}-snapshot.xlsx"

output_df.to_excel(output_filename, index=False)

print(f"✅ Saved daily snapshot: {output_filename}")
