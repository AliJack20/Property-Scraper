import csv
import re
import time
import contextlib
from urllib.parse import urlparse, urlunparse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D9%88%D8%B3%D8%B7-%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6?rent_period=eq,3"
PAGES_TO_SCRAPE = 19
OUTPUT_CSV = "aqar_listings_final.csv"

options_main = uc.ChromeOptions()
options_main.add_argument("--headless=new")
options_main.add_argument("--window-size=1920,1080")

options_detail = uc.ChromeOptions()
options_detail.add_argument("--headless=new")
options_detail.add_argument("--window-size=1920,1080")

driver = uc.Chrome(options=options_main)
detail_driver = uc.Chrome(options=options_detail)

all_listings = []

def click_translate_popup(driver):
    try:
        time.sleep(2)
        driver.execute_script("""
            function clickEnglishInIframe() {
                const iframes = document.querySelectorAll('iframe');
                for (let iframe of iframes) {
                    try {
                        const doc = iframe.contentDocument || iframe.contentWindow.document;
                        if (!doc) continue;

                        const buttons = doc.querySelectorAll('button');
                        for (let btn of buttons) {
                            if (btn.innerText.trim().toLowerCase() === 'english') {
                                btn.click();
                                return true;
                            }
                        }
                    } catch (e) {
                        continue;
                    }
                }
                return false;
            }

            const interval = setInterval(() => {
                if (clickEnglishInIframe()) {
                    clearInterval(interval);
                    console.log("✅ English clicked");
                }
            }, 500);
        """)
        time.sleep(4)
    except Exception as e:
        print(f"⚠️ Translate popup click failed: {e}")

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
    click_translate_popup(driver)
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
    for page in range(1, PAGES_TO_SCRAPE + 1):
        full_url = build_page_url(BASE_URL, page)
        print(f"\n🌐 Visiting page: {full_url}")
        driver.get(full_url)
        click_translate_popup(driver)
        time.sleep(5)

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
                title_element = card.find_element(By.CLASS_NAME, "_titleRow__1AWv1")
                title = title_element.text.strip()
            except:
                title = ""

            area, beds, baths = "", "", ""
            try:
                specs = card.find_elements(By.CLASS_NAME, "_spec__SIJiK")
                for spec in specs:
                    icon = spec.find_element(By.TAG_NAME, "img").get_attribute("alt")
                    value = spec.text.strip()
                    if "Area" in icon or "المساحة" in icon:
                        area = re.sub(r"[^\d,]", "", value)
                    elif "Bedrooms" in icon or "عدد الغرف" in icon:
                        beds = re.sub(r"[^\d]", "", value)
                    elif "Bathrooms" in icon or "عدد الحمامات" in icon:
                        baths = re.sub(r"[^\d]", "", value)
            except:
                pass

            features = extract_features_from_detail_page(detail_driver, url)
            print(f"✅ {title} | {price} SAR | {beds}BR | {baths}BA | {area} sqm | Features: {features}")

            all_listings.append({
                "URL": url,
                "Title": title,
                "Price": price,
                "Area": area,
                "Bedrooms": beds,
                "Bathrooms": baths,
                "Features": ", ".join(features)
            })

finally:
    with contextlib.suppress(Exception):
        driver.quit()
        detail_driver.quit()

with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=["URL", "Title", "Price", "Area", "Bedrooms", "Bathrooms", "Features"])
    writer.writeheader()
    for listing in all_listings:
        writer.writerow(listing)

print(f"\n✅ Scraping complete. {len(all_listings)} listings saved to {OUTPUT_CSV}")
