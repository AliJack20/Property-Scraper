import csv
import time
import re
from urllib.parse import urljoin

from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

# === Settings ===
BASE_URL = "https://www.booking.com/searchresults.en-gb.html?ssne=Riyadh&ssne_untouched=Riyadh&highlighted_hotels=7886346&ss=Riyadh&dest_id=900040280&dest_type=city&hp_avform=1&origin=hp&do_availability_check=1&label=en-pk-booking-desktop-4kfLJxx34ezdJh1Wp5MtEAS652796017653%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap%3Aneg%3Afi%3Atikwd-65526620%3Alp9077147%3Ali%3Adec%3Adm&aid=2311236&lang=en-gb&sb=1&src_elem=sb&src=hotel&checkin=2025-08-04&checkout=2025-08-07&group_adults=2&no_rooms=1&group_children=0"
PAGES_TO_SCRAPE = 1
OUTPUT_CSV = "booking_com_riyadh.csv"

# === Driver Setup ===
options = Options()
options.add_argument("start-maximized")
options.add_argument("--headless")  # Optional: remove if debugging
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(service=Service(), options=options)

# Stealth setup to avoid detection
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

all_listings = []

def extract_listing_urls():
    urls = []
    for page in range(PAGES_TO_SCRAPE):
        url = f"{BASE_URL}&offset={page * 25}"
        print(f"\n📄 Visiting: {url}")
        driver.get(url)
        time.sleep(5)

        cards = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="property-card"] a[data-testid="title-link"]')
        for card in cards:
            href = card.get_attribute("href")
            if href:
                urls.append(href.split("?")[0])  # Remove tracking query
    print(f"\n🔗 Collected {len(urls)} listing URLs")
    return urls

def get_outer_text_only(element: WebElement) -> str:
    """Returns only the outer text, excluding child elements."""
    return driver.execute_script("return arguments[0].childNodes[0].nodeValue.trim()", element)

def scrape_listing(url, idx, total):
    try:
        driver.get(url)
        print(f"\n🔍 Scraping {idx}/{total}: {url}")
        time.sleep(3)

        # Title
        try:
            title_elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h2.pp-header__title, h1'))
            )
            title = title_elem.text.strip()
        except:
            title = ""

        # Location
        try:
            location_elem = driver.find_element(By.CSS_SELECTOR, 'div.cb4b7a25d9.b06461926f')
            location = get_outer_text_only(location_elem)
        except:
            location = ""

        # Price
        try:
            price = driver.execute_script("""
                const priceElem = document.querySelector('span[data-testid="price-and-discounted-price"]');
                return priceElem ? priceElem.textContent.trim() : '';
            """)
            price = re.sub(r"[^\d]", "", price)
        except:
            price = ""

        # Rating
        try:
            rating = driver.execute_script("""
                const ratingDiv = document.querySelector('div.f63b14ab7a.dff2e52086');
                return ratingDiv ? ratingDiv.textContent.trim() : '';
            """)
        except:
            rating = ""

        # Amenities
        try:
            amenity_elems = driver.find_elements(By.CSS_SELECTOR, 'div[class*="hotel-facilities"] li')
            amenities = "; ".join([a.text.strip() for a in amenity_elems if a.text.strip()])
        except:
            amenities = ""

        print(title + " , " + location + ", " + rating + ", " + price + ", " + amenities)

        all_listings.append({
            "URL": url,
            "Title": title,
            "Location": location,
            "Price": price,
            "Rating": rating,
            "Amenities": amenities
        })

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")

try:
    listing_urls = extract_listing_urls()
    for i, link in enumerate(listing_urls, 1):
        scrape_listing(link, i, len(listing_urls))
finally:
    driver.quit()

# === Save to CSV ===
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["URL", "Title", "Location", "Price", "Rating", "Amenities"])
    writer.writeheader()
    writer.writerows(all_listings)

print(f"\n✅ Done. {len(all_listings)} listings saved to {OUTPUT_CSV}")
