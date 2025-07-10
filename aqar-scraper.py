from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# ✅ Setup Chrome with stealth
options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
# Uncomment headless if you want
# options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

stealth(driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

# ✅ Base URL
base_url = "https://sa.aqar.fm/شقق-للإيجار/الرياض/شمال-الرياض/حي-النرجس?beds=eq,3&rent_period=eq,3"

num_pages = 5  # How many pages you want

url_list = []

# ✅ Function to scrape all listing URLs on a page
def scrape_listing_urls():
    time.sleep(2)
    links = driver.find_elements(By.CSS_SELECTOR, 'a.card--clickable')
    urls = []
    for link in links:
        href = link.get_attribute("href")
        if href and href not in urls:
            urls.append(href)
    return urls

# ✅ Loop through pages
for page in range(1, num_pages + 1):
    if page == 1:
        url = base_url
    else:
        url = f"{base_url}&page={page}"
    print(f"Scraping page: {url}")
    driver.get(url)
    time.sleep(5)

    page_urls = scrape_listing_urls()
    print(f"Found {len(page_urls)} listings on page {page}")
    url_list.extend(page_urls)

print(f"Total URLs found: {len(url_list)}")

# ✅ Function to scrape details
def scrape_details_page(url):
    driver.get(url)
    time.sleep(3)
    data = {"URL": url}

    try:
        title = driver.find_element(By.CSS_SELECTOR, 'h1')
        data["Title"] = title.text.strip()
    except:
        data["Title"] = None

    try:
        price = driver.find_element(By.CSS_SELECTOR, 'span.price--text')
        data["Price"] = price.text.strip()
    except:
        data["Price"] = None

    try:
        # Beds/Baths/Area might be inside spans with class feature--item
        features = driver.find_elements(By.CSS_SELECTOR, 'span.feature--item')
        for feat in features:
            text = feat.text.strip()
            if "غرفة" in text or "غرف" in text:
                data["Beds"] = text
            elif "دورة" in text or "حمام" in text:
                data["Baths"] = text
            elif "متر" in text:
                data["Area"] = text
    except:
        data["Beds"] = data.get("Beds", None)
        data["Baths"] = data.get("Baths", None)
        data["Area"] = data.get("Area", None)

    print(data)
    return data

# ✅ Scrape each listing
results = []
for idx, url in enumerate(url_list):
    print(f"Scraping details ({idx + 1}/{len(url_list)})")
    details = scrape_details_page(url)
    results.append(details)

# ✅ Save to Excel
df = pd.DataFrame(results)
df.to_excel("aqarfm_properties.xlsx", index=False)
print("Saved to aqarfm_properties.xlsx")

driver.quit()
