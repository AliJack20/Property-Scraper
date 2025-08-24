import csv
import re
import time
from urllib.parse import urlparse, urlunparse

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/300"
PAGES_TO_SCRAPE = 75
OUTPUT_CSV = "aqar_listings_final.csv"

options = uc.ChromeOptions()
options.add_argument("--start-maximized")
driver = uc.Chrome(service=Service(), options=options)

all_listings = []

def build_page_url(base_url, page_number):
    parsed = urlparse(base_url)
    path = parsed.path.rstrip('/')
    segments = path.split('/')
    if segments[-1].isdigit():
        segments[-1] = str(page_number)
    else:
        segments.append(str(page_number))
    new_path = '/'.join(segments)
    return urlunparse(parsed._replace(path=new_path))

def extract_features_from_detail_page(driver, url):
    driver.get(url)
    #click_translate_popup(driver)
    time.sleep(4)

    features = []
    try:
        labels = driver.find_elements(By.CLASS_NAME, "_label___qjLO")
        for label in labels:
            if "checkmark.svg" in label.get_attribute("innerHTML"):
                features.append(label.text.strip())
    except Exception as e:
        print(f"⚠️ Feature extraction error: {e}")
    return features

try:
    listing_urls = []

    # Step 1: Gather listing URLs from all pages
    for page in range(1, PAGES_TO_SCRAPE + 1):
        full_url = build_page_url(BASE_URL, page)
        print(f"\n📄 Visiting page: {full_url}")
        driver.get(full_url)
        time.sleep(5)

        cards = driver.find_elements(By.CLASS_NAME, "_listingCard__PoR_B")
        if not cards:
            print(f"No listings found on page {page}")
            continue

        print(f"Found {len(cards)} listings on page {page}")

        for card in cards:
            try:
                parent_a = card.find_element(By.XPATH, "./ancestor::a[1]")
                href = parent_a.get_attribute("href")
                full_url = href if href.startswith("http") else "https://sa.aqar.fm" + href
                listing_urls.append(full_url)
            except Exception as e:
                print(f"⚠️ Could not get URL for a card: {e}")
                continue

    print(f"\n🔗 Collected {len(listing_urls)} listing URLs")

    # Step 2: Visit each listing and scrape data
    for idx, url in enumerate(listing_urls, 1):
        try:
            driver.get(url)
            print(f"\n🔍 Scraping listing {idx}/{len(listing_urls)}: {url}")
            time.sleep(3)

            # Extract price
            try:
                price = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "_price__X51mi"))
                ).text
                #price = re.sub(r"[^\d,]", "", price).strip()
            except:
                price = ""

            # Extract title
            try:
                title_elem = driver.find_element(By.CLASS_NAME, "_title__eliuu")
                title = title_elem.text.strip()
            except:
                title = ""


            # Extract specs (area, beds, baths)
            try:
                specs = driver.find_elements(By.CLASS_NAME, "_spec__SIJiK")
                area = beds = baths = ""
                for spec in specs:
                    icon = spec.find_element(By.TAG_NAME, "img").get_attribute("alt")
                    value = spec.text.strip()
                    if "المساحة" in icon:
                        area = re.sub(r"[^\d,]", "", value)
                    elif "عدد الغرف" in icon:
                        beds = re.sub(r"[^\d]", "", value)
                    elif "عدد الحمامات" in icon:
                        baths = re.sub(r"[^\d]", "", value)
            except:
                area = beds = baths = ""

            # Extract features (amenities)
            features_str = extract_features_from_detail_page(driver, url)
            print(f"✅ Scraped: {title}, {price}, {beds}BR, {baths}BA, {area}sqm, Features: {features_str}")

            all_listings.append({
                "URL": url,
                "Title": title,
                "Price": price,
                "Area": area,
                "Bedrooms": beds,
                "Bathrooms": baths,
                "Features": features_str
            })

        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            continue

finally:
    driver.quit()

# Save to CSV
with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=["URL","Title", "Price", "Area", "Bedrooms", "Bathrooms", "Features"])
    writer.writeheader()
    for listing in all_listings:
        writer.writerow(listing)

print(f"\n📁 Done. {len(all_listings)} listings saved to {OUTPUT_CSV}")
