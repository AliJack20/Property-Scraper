from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from selenium.common.exceptions import NoSuchElementException
import time
import re
import pandas as pd

# Setup Chrome with stealth options
options = Options()
options.add_argument("start-maximized")
# options.add_argument("--headless")  # Enable if needed
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

# Function to scrape all property URLs from current page
def scrape_current_page():
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/rooms/"]')
    urls = []
    for link in links:
        href = link.get_attribute("href")
        if href and "/rooms/" in href:
            urls.append(href.split("?")[0])
    return list(set(urls))

# Scroll to bottom to load dynamic listings
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

# Function to scrape details from individual listing page
def scrape_details_page(url):
    try:
        driver.get(url)
        time.sleep(2)
        scroll_to_bottom_incrementally()
        html = driver.page_source

        title = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        # Improved price extraction logic
        discounted_price_match = re.search(r'<span class="umuerxh[^"]*">\$?([\d,]+)</span>', html)
        if discounted_price_match:
            price = f"${discounted_price_match.group(1)}"
        else:
            # Fall back to original price
            original_price_match = re.search(r'<span class="s13lowb4[^"]*">\$?([\d,]+)</span>', html)
            if original_price_match:
                price = f"${original_price_match.group(1)}"
            else:
                price = None

        address = re.search(r'dir-ltr"><div[^>]+><section><div[^>]+ltr"><h2[^>]+>([^<]+)</h2>', html)
        guest = re.search(r'<li class="l7n4lsf[^>]+>([^<]+)<span', html)
        reviews_match = re.search(r'<span[^>]*aria-hidden="true"[^>]*>([\d.]+)\s*·\s*(\d+)\s*reviews</span>', html)
        host_name = re.search(r't1gpcl1t[^>]+>([^<]+)</div>', html)
        host_info = re.findall(r'd1u64sg5[^"]+atm_67_1vlbu9m[^>]*><div><span[^>]*>([^<]+)', html)

        # Extract all <li> elements with that class
        bed_bath_lis = re.findall(r'<li[^>]*class="l7n4lsf[^"]*"[^>]*>(.*?)</li>', html, re.DOTALL)
        bed_bath_details = []

        for item in bed_bath_lis:
            text = re.sub(r'<[^>]+>', '', item)  # Strip HTML tags
            text = text.replace("·", "").strip()
            if any(x in text.lower() for x in ["bed", "bath", "bedroom"]):
                bed_bath_details.append(text)


        amenities = []
        try:
            amenity_blocks = driver.find_elements(By.CSS_SELECTOR, 'div._19xnuo97')
            for block in amenity_blocks:
                try:
                    name_elem = block.find_element(By.CSS_SELECTOR, 'div.iikjzje > div')
                    name = name_elem.text.strip()
                    if name:
                        amenities.append(name)
                except:
                    continue
        except:
            pass

        return {
            "URL": url,
            "Title": title.group(1) if title else None,
            "Price (5 Nights)": price,
            "Address": address.group(1) if address else None,
            "Guest": guest.group(1) if guest else None,
            "Bed_Bath_Details": bed_bath_details,
            "Rating": reviews_match.group(1) if reviews_match else None,
            "Total_Reviews": reviews_match.group(2) if reviews_match else None,
            "Host_Name": host_name.group(1) if host_name else None,
            "Host_Info": host_info,
            "Amenities": amenities
        }

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None

# Save final scraped data to CSV
def save_to_csv(data, filename='airbnb_riyadh_data.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"✅ Data saved to {filename}")

# Start scraping
base_url = "https://www.airbnb.com/s/Riyadh--Riyadh-Region--Saudi-Arabia/homes?flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2025-08-01&monthly_length=3&monthly_end_date=2025-11-01&place_id=ChIJbzwfOtKkLz4R5yvDtOxu8y4&refinement_paths%5B%5D=%2Fhomes&acp_id=d67b445a-d3a3-4dc9-be4f-15cc744ea123&date_picker_type=calendar&source=structured_search_input_header&search_type=unknown&query=Riyadh%2C%20Riyadh%20Region%2C%20Saudi%20Arabia&search_mode=regular_search&price_filter_input_type=2&price_filter_num_nights=5&channel=EXPLORE&checkin=2025-07-21&checkout=2025-07-25"
driver.get(base_url)

WebDriverWait(driver, 20).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/rooms/"]'))
)
scroll_to_bottom_incrementally()

url_list = scrape_current_page()
print(f"✅ Found {len(url_list)} listings")

scraped_data = []
for i, link in enumerate(url_list):
    print(f"🔎 Scraping {i+1}/{len(url_list)}: {link}")
    result = scrape_details_page(link)
    print(f"[{link}] Scraped Data: {result}") 
    if result:
        scraped_data.append(result)

if scraped_data:
    save_to_csv(scraped_data)
else:
    print("❌ No data scraped.")

driver.quit()