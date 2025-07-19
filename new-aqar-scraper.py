import csv
import re
import time
import contextlib
from urllib.parse import urlparse, urlunparse

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc


BASE_URL = "https://sa.aqar.fm/شقق-للإيجار/الرياض/شمال-الرياض/حي-النرجس?rent_period=eq,3&beds=eq,2"
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
    segments = path.split('/')
    if segments[-1].isdigit():
        segments[-1] = str(page_number)
    else:
        segments.append(str(page_number))
    new_path = '/'.join(segments)
    return urlunparse(parsed._replace(path=new_path))

def get_cookies_dict(driver):
    cookies = driver.get_cookies()
    return {cookie['name']: cookie['value'] for cookie in cookies}

def get_phone_number(url, driver):
    """
    Uses requests (with Selenium cookies) to fetch the detail page and extract the phone number.
    The response encoding is forced to UTF-8 to avoid latin-1 codec errors.
    The function searches for a Saudi phone number pattern (e.g. 05XXXXXXXX).
    """
    cookies = get_cookies_dict(driver)
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/117.0 Safari/537.36"),
        "Referer": BASE_URL,
    }
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        response.encoding = 'utf-8'  # Force UTF-8 decoding
        if response.status_code == 200:
            match = re.search(r'(?:(?:\+966|0)?5\d{8})', response.text)
            return match.group(0) if match else ""
        else:
            print(f"❌ Failed to fetch {url} | Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
    return ""

try:
    for page in range(1, PAGES_TO_SCRAPE + 1):
        full_url = build_page_url(BASE_URL, page)
        print(f"\nVisiting: {full_url}")
        driver.get(full_url)
        time.sleep(5)  # Allow page to load fully

        cards = driver.find_elements(By.CLASS_NAME, "_listingCard__PoR_B")
        if not cards:
            print(f"No listings found on page {page}")
            continue

        print(f"Found {len(cards)} listings on page {page}")

        for card in cards:
            try:
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
                except:
                    area = beds = baths = ""

                # Get phone number using requests instead of Selenium to avoid blocking
                phone = get_phone_number(url, driver)
                print(f"Phone found: {phone}")

                all_listings.append({
                    "URL": url,
                    "Price": price,
                    "Area": area,
                    "Bedrooms": beds,
                    "Bathrooms": baths,
                    "Phone": phone
                })

                time.sleep(1)  # slight delay between listings

            except Exception as e:
                print(f"Error parsing card: {e}")
                continue

finally:
    from contextlib import suppress
    with suppress(Exception):
        driver.quit()

# Write CSV
with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["URL", "Price", "Area", "Bedrooms", "Bathrooms", "Phone"])
    writer.writeheader()
    for listing in all_listings:
        writer.writerow(listing)

print(f"\n✅ Scraping finished. {len(all_listings)} listings saved to {OUTPUT_CSV}")
