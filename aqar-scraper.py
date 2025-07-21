import csv
import re
import time
import contextlib
from urllib.parse import urlparse, urlunparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc


BASE_URL = "https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%B4%D9%85%D8%A7%D9%84-%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%AD%D9%8A-%D8%A7%D9%84%D9%86%D8%B1%D8%AC%D8%B3?rent_period=eq,3&beds=eq,2"
PAGES_TO_SCRAPE = 1
OUTPUT_CSV = "aqar_listings_final.csv"


options = uc.ChromeOptions()
options.add_argument("--start-maximized")

service = Service()
driver = uc.Chrome(service=service, options=options)

all_listings = []

def build_page_url(base_url, page_number):
    parsed = urlparse(base_url)
    path = parsed.path.rstrip('/')

    # If last segment is a digit -> replace it
    segments = path.split('/')
    if segments[-1].isdigit():
        segments[-1] = str(page_number)
    else:
        segments.append(str(page_number))

    new_path = '/'.join(segments)
    new_url = urlunparse(parsed._replace(path=new_path))
    return new_url

try:
    for page in range(1, PAGES_TO_SCRAPE + 1):
        full_url = build_page_url(BASE_URL, page)
        print(f"Visiting: {full_url}")
        driver.get(full_url)
        time.sleep(5)  # adjust for page load

        cards = driver.find_elements(By.CLASS_NAME, "_listingCard__PoR_B")
        if not cards:
            print(f"No listings found on page {page}")
            continue

        for card in cards:
            parent_a = card.find_element(By.XPATH, "./ancestor::a[1]")
            href = parent_a.get_attribute("href")
            if href.startswith("http"):
                url = href
            else:
                url = "https://sa.aqar.fm" + href

            try:
                price = card.find_element(By.CLASS_NAME, "_price__X51mi").text
                price = re.sub(r"[^\d,]", "", price).strip()
            except:
                price = ""

            try:
                specs = card.find_elements(By.CLASS_NAME, "_spec__SIJiK")
                area, beds, baths = "", "", ""

                for spec in specs:
                    icon = spec.find_element(By.TAG_NAME, "img").get_attribute("alt")
                    value = spec.text.strip()
                    if "المساحة" in icon:
                        area = re.sub(r"[^\d,]", "", value)
                    elif "عدد الغرف" in icon:
                        beds = re.sub(r"[^\d]", "", value)
                    elif "عدد الحمامات" in icon:
                        baths = re.sub(r"[^\d]", "", value)

                all_listings.append({
                    "URL": url,
                    "Price": price,
                    "Area": area,
                    "Bedrooms": beds,
                    "Bathrooms": baths
                })
            except Exception as e:
                print(f"Error parsing card: {e}")

finally:
    with contextlib.suppress(Exception):
        driver.quit()


with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["URL", "Price", "Area", "Bedrooms", "Bathrooms"])
    writer.writeheader()
    for listing in all_listings:
        writer.writerow(listing)

print(f"\n✅ Scraping finished. {len(all_listings)} listings saved to {OUTPUT_CSV}")
