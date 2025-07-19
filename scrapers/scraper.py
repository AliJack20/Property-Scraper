import pandas as pd
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from google.cloud import bigquery, storage


# ---------- Load your approved comp-set ----------
df = pd.read_excel("properties.xlsx")
properties = df.to_dict(orient="records")

# ---------- Your scraper -----------
async def scrape_one(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        # Wait for calendar or price elements to load
        await page.wait_for_selector("h1")

        # Example extraction — you'll adjust selectors
        title = await page.locator("h1").inner_text()
        # Add calendar scraping logic here (loop through months, prices, etc.)

        result = {
            "property_url": url,
            "title": title,
            "scraped_on": datetime.today().strftime('%Y-%m-%d'),
            "adr_next_7d": 150,
            "adr_rest_month": 140,
            "adr_next_month": 155,
            "cleaning_fee": 50,
            "min_stay": 2,
            "review_score": 4.8,
            "num_reviews": 85,
            "free_days_60d": 35,
        }

        await browser.close()
        return result



async def main():
    tasks = [scrape_one(p['URL']) for p in properties]
    results = await asyncio.gather(*tasks)

    df_out = pd.DataFrame(results)
    filename = f"{datetime.today().strftime('%Y-%m-%d')}-comp-snapshot.csv"
    df_out.to_csv(filename, index=False)
    print(f"✅ Saved daily snapshot to {filename}")

    upload_to_bigquery(
    df=df_out,
    project_id="your-gcp-project-id",
    dataset_id="your_dataset",
    table_name="comp_tracker"
)

    # Upload to GCS or BigQuery here
    # Example: upload_to_gcs(filename)
    # Example: upload_to_bigquery(df_out)

asyncio.run(main())
