from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import pandas as pd

# =========================
# Browser Setup
# =========================
options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options)

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)

# =========================
# Login with Magic Link
# =========================
def login_with_magic_link():
    magic_url = input("Paste your AirDNA magic login link: ").strip()
    driver.get(magic_url)
    print("🔑 Opening magic link...")

    # Give it time to establish session
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(5)
    print("✅ Logged in successfully.")

# =========================
# Scroll Function
# =========================
def scroll_to_bottom_incrementally():
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# =========================
# Card Scraper
# =========================
def scrape_property_cards_from_market():
    cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/property/']")
    seen = set()
    urls = []
    for card in cards:
        link = card.get_attribute("href")
        if link and link not in seen:
            urls.append(link)
            seen.add(link)
    return urls

# =========================
# Detail Page Scraper
# =========================
def scrape_details_page(url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        scroll_to_bottom_incrementally()

        def safe_get(selector, attr="text"):
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                return el.text.strip() if attr == "text" else el.get_attribute(attr)
            except NoSuchElementException:
                return None

        name = safe_get("h1.property-title")
        market_score = safe_get(".market-score")
        ptype = safe_get(".property-type")
        price_tier = safe_get(".price-tier")
        bed_bath_guest = safe_get(".beds-baths-guests")
        rating = safe_get(".rating-value")
        reviews = safe_get(".reviews-count")
        rev_potential = safe_get(".rev-potential")
        days_available = safe_get(".days-available")
        annual_revenue = safe_get(".annual-revenue")
        occupancy = safe_get(".occupancy")
        adr = safe_get(".adr")

        try:
            amenities_elements = driver.find_elements(By.CSS_SELECTOR, ".amenities-list li")
            amenities = [a.text.strip() for a in amenities_elements if a.text.strip()]
        except:
            amenities = []

        return {
            "Name": name,
            "Market Score": market_score,
            "Type": ptype,
            "Price Tier": price_tier,
            "Bed,Bath,Guest": bed_bath_guest,
            "Rating": rating,
            "Reviews": reviews,
            "Revenue Potential": rev_potential,
            "Days Available": days_available,
            "Annual Revenue": annual_revenue,
            "Occupancy": occupancy,
            "ADR": adr,
            "Amenities": amenities,
            "URL": url
        }

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None

# =========================
# Save to CSV
# =========================
def save_to_csv(data, filename='airdna_data.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"✅ Data saved to {filename}")

# =========================
# Main Flow
# =========================
login_with_magic_link()

target_url = "https://app.airdna.co/data/sa/102130?lat=23.530462&lng=45.141804&zoom=5"
driver.get(target_url)
time.sleep(5)

scroll_to_bottom_incrementally()
property_urls = scrape_property_cards_from_market()
print(f"Found {len(property_urls)} property URLs.")

scraped_data = []
for link in property_urls:
    print(f"Scraping {link} ...")
    details = scrape_details_page(link)
    if details:
        scraped_data.append(details)

save_to_csv(scraped_data)
driver.quit()
