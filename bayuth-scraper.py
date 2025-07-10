from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
# options.add_argument("--headless")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options)

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

# 📌 Updated selectors for Bayut

# Function to scrape all property URLs on current page
def scrape_current_page():
    links = driver.find_elements(By.CSS_SELECTOR, 'a[aria-label][href*="/property/"]')
    urls = []
    for link in links:
        href = link.get_attribute("href")
        if href not in urls:
            urls.append(href)
    return urls

# Scroll down to load listings
def scroll_to_bottom_incrementally():
    SCROLL_PAUSE_TIME = 1
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Try to click next page
def go_to_next_page():
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[aria-label="Next"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(1)
        next_button.click()
        return True
    except:
        return False

# ✅ BAYUT URL
# Base URL WITHOUT page
base_url = "https://www.bayut.sa/en/to-rent/3-bedroom-properties/riyadh/north-riyadh/al-narjis/?rent_frequency=yearly&sort=price_desc&furnishing_status=unfurnished"

num_pages = 5  # however many pages you want

url_list = []

for page in range(1, num_pages + 1):
    if page == 1:
        url = base_url
    else:
        url = f"{base_url}&page={page}"
    
    print(f"Scraping: {url}")
    driver.get(url)
    time.sleep(3)
    
    # If listings load on scroll, keep your scroll here:
    scroll_to_bottom_incrementally()

    page_urls = scrape_current_page()
    url_list.extend(page_urls)
    print(f"Found {len(page_urls)} listings on page {page}")

print(f"Total listings scraped: {len(url_list)}")

# Scrape details page for each property
def scrape_details_page(url):
    driver.get(url)
    time.sleep(3)
    data = {}
    data["URL"] = url

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

    # ✅ Get visible amenities first
    
    # ===============================
# In your scrape_details_page
# ===============================

    # === Scrape always-visible amenities ===
    amenities = []

    try:
        # Get visible amenity blocks
        visible_blocks = driver.find_elements(By.CSS_SELECTOR, 'div._117b341a')
        for block in visible_blocks:
            spans = block.find_elements(By.CSS_SELECTOR, 'span._7181e5ac')
            for span in spans:
                text = span.text.strip()
                if text and text not in amenities:
                    amenities.append(text)
    except Exception as e:
        print(f"Could not get visible amenities: {e}")

    # === Now check for `+ more` button and scrape hidden ones ===
    try:
        more_button = driver.find_element(By.CSS_SELECTOR, 'div._6e45c68c[aria-label*="More amenities"]')
        if more_button.is_displayed():
            driver.execute_script("arguments[0].click();", more_button)
            # Wait for modal to appear
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#property-amenity-dialog'))
            )
            # Scrape amenities inside modal
            modal_spans = driver.find_elements(By.CSS_SELECTOR, '#property-amenity-dialog span._7181e5ac')
            for span in modal_spans:
                text = span.text.strip()
                if text and text not in amenities:
                    amenities.append(text)

            # OPTIONAL: Close modal
            try:
                close_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Close button"]')
                driver.execute_script("arguments[0].click();", close_button)
            except:
                pass
    except Exception as e:
        print(f"No more amenities button or could not open modal: {e}")

    # === Save to your result dict ===
    data["Amenities"] = ", ".join(amenities)



    print(data)
    return data

# Save to Excel
def save_to_excel(data, filename='bayut_al_narjis(2)_properties.xlsx'):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Data saved to {filename}")

scraped_data = []

for url in url_list:
    details = scrape_details_page(url)
    scraped_data.append(details)

save_to_excel(scraped_data)

driver.quit()
