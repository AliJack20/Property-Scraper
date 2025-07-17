from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from selenium.common.exceptions import TimeoutException

# === Setup ChromeOptions ===
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
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
    return driver

# === Login Function ===
def login(driver, email, password):
    try:
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Login"]'))
        )
        login_btn.click()
        time.sleep(2)
    except Exception as e:
        print("❌ Login button click failed:", e)
        return False

    try:
        login_with_email = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Login with Email"]'))
        )
        login_with_email.click()
        time.sleep(2)
    except Exception as e:
        print("❌ Login with email click failed:", e)
        return False

    try:
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))
        )
        password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        email_input.send_keys(email)
        password_input.send_keys(password)
        time.sleep(1)
    except Exception as e:
        print("❌ Failed to input credentials:", e)
        return False

    try:
        final_login_btn = driver.find_element(By.CSS_SELECTOR, 'button._91e21052')
        final_login_btn.click()
        print("✅ Login form submitted.")
    except Exception as e:
        print("❌ Final login button click failed:", e)
        return False

    # ✅ Wait for either user account OR disappearance of Login button
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "LivedIn")]'))
        )
        print("✅ Logged in - found account button.")
        return True
    except TimeoutException:
        try:
            # Check if "Login" button disappeared
            WebDriverWait(driver, 5).until_not(
                EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Login"]'))
            )
            print("✅ Logged in - login button disappeared.")
            return True
        except TimeoutException:
            driver.save_screenshot("login_check_failed.png")
            print("❌ Login failed - still sees login button. Screenshot saved.")
            return False

# === Scroll and URL Collection ===
def scroll_to_bottom_incrementally(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_current_page(driver):
    links = driver.find_elements(By.CSS_SELECTOR, 'a[aria-label][href*="/property/"]')
    urls = []
    for link in links:
        href = link.get_attribute("href")
        if href not in urls:
            urls.append(href)
    return urls

# === Scrape Individual Listing ===
def scrape_details_page(driver, url):
    print(f"🧪 Using shared driver session on: {url}")
    driver.get(url)
    time.sleep(2)
    data = {"URL": url}

    try:
        title_elem = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1'))
        )
        data["Title"] = title_elem.text.strip()
    except:
        data["Title"] = None

    try:
        price_elem = driver.find_element(By.CSS_SELECTOR, '[aria-label="Price"]')
        data["Price"] = price_elem.text.strip()
    except:
        data["Price"] = None

    try:
        beds_elem = driver.find_element(By.CSS_SELECTOR, '[aria-label="Beds"]')
        data["Beds"] = beds_elem.text.strip()
    except:
        data["Beds"] = None

    try:
        baths_elem = driver.find_element(By.CSS_SELECTOR, '[aria-label="Baths"]')
        data["Baths"] = baths_elem.text.strip()
    except:
        data["Baths"] = None

    try:
        size_elem = driver.find_element(By.CSS_SELECTOR, '[aria-label="Area"]')
        data["Area"] = size_elem.text.strip()
    except:
        data["Area"] = None

    # === Amenities Extraction ===
    amenities = []
    try:
        visible_blocks = driver.find_elements(By.CSS_SELECTOR, 'div._117b341a')
        for block in visible_blocks:
            spans = block.find_elements(By.CSS_SELECTOR, 'span._7181e5ac')
            for span in spans:
                text = span.text.strip()
                if text and text not in amenities:
                    amenities.append(text)
    except:
        pass

    try:
        more_button = driver.find_element(By.CSS_SELECTOR, 'div._6e45c68c[aria-label*="More amenities"]')
        if more_button.is_displayed():
            driver.execute_script("arguments[0].click();", more_button)
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#property-amenity-dialog'))
            )
            modal_spans = driver.find_elements(By.CSS_SELECTOR, '#property-amenity-dialog span._7181e5ac')
            for span in modal_spans:
                text = span.text.strip()
                if text and text not in amenities:
                    amenities.append(text)
    except:
        pass

    data["Amenities"] = ", ".join(amenities)
    print(data)
    return data

# === Main Execution ===
EMAIL = 'support@livedin.co'
PASSWORD = 'Livedin2025!'

base_url = "https://www.bayut.sa/en/to-rent/2,3-bedroom-properties/riyadh/north-riyadh/al-narjis/?rent_frequency=yearly&sort=price_desc&furnishing_status=unfurnished"

# === Create Driver Once ===
driver = create_driver()
driver.get(base_url)

# === Login Once ===
if not login(driver, EMAIL, PASSWORD):
    print("❌ Login failed. Exiting.")
    driver.quit()
    exit()

# === Get Listing URLs ===
num_pages = 1
url_list = []
for page in range(1, num_pages + 1):
    url = base_url if page == 1 else f"{base_url}&page={page}"
    print(f"🔎 Scraping: {url}")
    driver.get(url)
    time.sleep(3)
    scroll_to_bottom_incrementally(driver)
    page_urls = scrape_current_page(driver)
    print(f"✅ Found {len(page_urls)} on page {page}")
    url_list.extend(page_urls)

# === Scrape Details in SAME Session ===
scraped_data = []
for idx, url in enumerate(url_list):
    print(f"🔍 Scraping detail ({idx + 1}/{len(url_list)})")
    details = scrape_details_page(driver, url)
    scraped_data.append(details)

# === Save and Close ===
driver.quit()
df = pd.DataFrame(scraped_data)
df.to_excel("bayut_final_properties.xlsx", index=False)
print("✅ Saved all data!")