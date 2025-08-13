from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import re
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
# Login Function
# =========================
def login_to_airdna():
    email = "ali.siddiqui@livedin.co"

    # Step 1: Go to AirDNA login page
    driver.get("https://www.airdna.co/login")

    # Step 2: Click the "Log in" button that triggers the popup
    try:
        login_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Log in")]'))
        )
        driver.execute_script("arguments[0].click();", login_btn)
        print("🔄 Login popup opened...")
    except Exception as e:
        print("❌ Could not click initial Log in button:", e)
        return False

    # Step 3: Wait for email input in popup
    try:
        email_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "loginId"))
        )
        email_input.send_keys(email)
        print("📨 Email entered.")
    except Exception as e:
        print("❌ Could not find email input in popup:", e)
        return False

    # Step 4: Click "Send me a login link" button
    try:
        send_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Send me a login link")]'))
        )
        driver.execute_script("arguments[0].click();", send_btn)
        print("✅ Login link requested. Check your email.")

        # Stop AirDNA from redirecting to another page
        time.sleep(1)  # small wait to ensure click event fires
        driver.execute_script("window.stop();")
        print("⏸️ Redirect stopped. Waiting for magic link...")
    except Exception as e:
        print("❌ Could not click send login link button:", e)
        return False


    # Step 5: Freeze here until user pastes link
    print("\n📧 Waiting for you to paste the magic login link...")
    magic_url = input("Paste the magic login link from your email and press Enter: ").strip()

    # Step 6: Go directly to magic link
    driver.get(magic_url)
    WebDriverWait(driver, 15).until(EC.url_contains("app.airdna.co"))
    print("✅ Logged in successfully via magic link.")

    return True



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

        name = safe_get("h1.property-title")  # Update selector
        market_score = safe_get(".market-score")  # Update selector
        ptype = safe_get(".property-type")  # Update selector
        price_tier = safe_get(".price-tier")  # Update selector
        bed_bath_guest = safe_get(".beds-baths-guests")  # Update selector
        rating = safe_get(".rating-value")  # Update selector
        reviews = safe_get(".reviews-count")  # Update selector
        rev_potential = safe_get(".rev-potential")  # Update selector
        days_available = safe_get(".days-available")  # Update selector
        annual_revenue = safe_get(".annual-revenue")  # Update selector
        occupancy = safe_get(".occupancy")  # Update selector
        adr = safe_get(".adr")  # Update selector

        # Amenities list
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
login_to_airdna()
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
