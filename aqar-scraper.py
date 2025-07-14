from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import pandas as pd

# -----------------------------------------------
# ✅ 1️⃣ Setup Selenium
# -----------------------------------------------

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# options.add_argument("--headless")  # Uncomment if you want headless mode

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# -----------------------------------------------
# ✅ 2️⃣ Base config
# -----------------------------------------------

base_url = "https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%B4%D9%85%D8%A7%D9%84-%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%AD%D9%8A-%D8%A7%D9%84%D9%86%D8%B1%D8%AC%D8%B3?beds=eq,3&rent_period=eq,3"
all_links = []
aqar = "https://sa.aqar.fm"

# -----------------------------------------------
# ✅ 3️⃣ Loop through pages and collect listing URLs
# -----------------------------------------------

num_pages = 3  # Change this to as many pages as you want
for i in range(1, num_pages + 1):
    url = f"{base_url}{i}"
    driver.get(url)
    print(f"Scraping: {url}")

    try:
        # Wait for at least one listing link to appear
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/listing/"]'))
        )
    except:
        print(f"No listings found on page {i}")
        continue

    # Get all listing links
    offers = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/listing/"]')

    page_links = []
    for offer in offers:
        href = offer.get_attribute("href")
        if href and href.startswith("/listing/"):
            full_url = f"{aqar}{href}"
            if full_url not in all_links:
                page_links.append(full_url)

    print(f"Page {i}: Found {len(page_links)} listings.")
    all_links.extend(page_links)

print(f"✅ Total unique listings found: {len(all_links)}")

# -----------------------------------------------
# ✅ 4️⃣ Scrape details from each listing page
# -----------------------------------------------

main_location = []
sub_location = []
hood = []
size = []
pricepm = []
frontage = []
purpose = []
street_width = []

for idx, listing_url in enumerate(all_links):
    print(f"Scraping ({idx + 1}/{len(all_links)}): {listing_url}")
    driver.get(listing_url)
    sleep(2)

    # Breadcrumbs for location
    try:
        tree = driver.find_elements(By.CSS_SELECTOR, 'a.treeLink')
        if len(tree) > 3:
            main_location.append(tree[1].text.strip())
            sub_location.append(tree[2].text.strip())
            hood.append(tree[3].text.strip())
        else:
            main_location.append(tree[1].text.strip())
            sub_location.append(None)
            hood.append(tree[2].text.strip())
    except:
        main_location.append(None)
        sub_location.append(None)
        hood.append(None)

    # Table details
    try:
        table = driver.find_elements(By.CSS_SELECTOR, 'td[align="right"][dir="rtl"]')
        size.append(table[0].text.strip() if len(table) > 0 else None)
        pricepm.append(table[2].text.strip() if len(table) > 2 else None)
        frontage.append(table[4].text.strip() if len(table) > 4 else None)
        purpose.append(table[6].text.strip() if len(table) > 6 else None)
        street_width.append(table[8].text.strip() if len(table) > 8 else None)
    except:
        size.append(None)
        pricepm.append(None)
        frontage.append(None)
        purpose.append(None)
        street_width.append(None)

# -----------------------------------------------
# ✅ 5️⃣ Save to CSV
# -----------------------------------------------

df = pd.DataFrame({
    "main_location": main_location,
    "sub_location": sub_location,
    "hood": hood,
    "size": size,
    "price_per_meter": pricepm,
    "frontage": frontage,
    "purpose": purpose,
    "street_width": street_width
})

print(df.head())
df.to_csv("aqardata_final.csv", index=False)
print("✅ Saved to aqardata_final.csv")

# -----------------------------------------------
# ✅ 6️⃣ Done!
# -----------------------------------------------
