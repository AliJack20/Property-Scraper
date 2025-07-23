import csv
import re
import time
import contextlib
from urllib.parse import urlparse, urlunparse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%B4%D9%85%D8%A7%D9%84-%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%AD%D9%8A-%D8%A7%D9%84%D9%86%D8%B1%D8%AC%D8%B3?rent_period=eq,3&beds=eq,2"
PAGES_TO_SCRAPE = 1
OUTPUT_CSV = "aqar_listings_final.csv"

options_main = uc.ChromeOptions()
options_main.add_argument("--start-maximized")

options_detail = uc.ChromeOptions()
options_detail.add_argument("--start-maximized")

driver = uc.Chrome(options=options_main)
detail_driver = uc.Chrome(options=options_detail)


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

def click_translate_popup(driver):
    try:
        time.sleep(1)
        for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
            try:
                driver.switch_to.frame(iframe)
                button = driver.find_element(By.XPATH, "//button[contains(text(), 'English')]")
                button.click()
                print("🌍 Clicked 'English' on Google Translate popup.")
                time.sleep(1)
                break
            except:
                driver.switch_to.default_content()
        driver.switch_to.default_content()
    except Exception as e:
        print(f"⚠️ Could not handle translate popup: {e}")


def extract_features_from_detail_page(driver, url):
    driver.get(url)
    time.sleep(2)  # Wait for page to load (adjust as needed)

    features = []
    try:
        labels = driver.find_elements(By.CLASS_NAME, "_label___qjLO")
        for label in labels:
            try:
                # Only include labels that contain the checkmark icon
                if "checkmark.svg" in label.get_attribute("innerHTML"):
                    features.append(label.text.strip())
            except Exception:
                continue
    except Exception as e:
        print(f"Error extracting features: {e}")
    return features



try:
    for page in range(1, PAGES_TO_SCRAPE + 1):
        full_url = build_page_url(BASE_URL, page)
        print(f"\n🌐 Visiting page: {full_url}")
        driver.get(full_url)
        click_translate_popup(driver)
        time.sleep(3)

        cards = driver.find_elements(By.CLASS_NAME, "_listingCard__PoR_B")
        if not cards:
            print(f"❌ No listings found on page {page}")
            continue

        for card in cards:
            try:
                parent_a = card.find_element(By.XPATH, "./ancestor::a[1]")
                href = parent_a.get_attribute("href")
                url = href if href.startswith("http") else "https://sa.aqar.fm" + href
            except:
                continue

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
                area, beds, baths = "", "", ""

            features = extract_features_from_detail_page(detail_driver, url)
            print(f"✅ {price} SAR | {beds}BR | {baths}BA | {area} sqm | Features: {features}")

            all_listings.append({
                "URL": url,
                "Price": price,
                "Area": area,
                "Bedrooms": beds,
                "Bathrooms": baths,
                "Features": features
            })

finally:
    with contextlib.suppress(Exception):
        driver.quit()
        detail_driver.quit()

with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=["URL", "Price", "Area", "Bedrooms", "Bathrooms", "Features"])
    writer.writeheader()
    for listing in all_listings:
        writer.writerow(listing)


print(f"\n✅ Scraping complete. {len(all_listings)} listings saved to {OUTPUT_CSV}")