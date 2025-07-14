from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import pandas as pd
import re

# ------------- Setup Chrome -------------
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
    fix_hairline=True,
)

# ------------- Helpers -------------

def scrape_current_page():
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/rooms/"]')
    urls = []
    for link in links:
        href = link.get_attribute("href")
        if "/rooms/" in href and href not in urls:
            urls.append(href)
    return urls


def scroll_and_collect_more(previous_count):
    SCROLL_PAUSE_TIME = 3

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)

    new_links = scrape_current_page()
    print(f"Found {len(new_links)} links after scroll.")
    return len(new_links) > previous_count



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


def scrape_details_page(url):
    try:
        driver.get(url)
        time.sleep(2)
        scroll_to_bottom_incrementally()
        time.sleep(2)

        html_content = driver.page_source

        # Title by regex
        title_pattern = r'<h1[^>]+>([^<]+)</h1>'
        title = re.search(title_pattern, html_content)
        title = title.group(1).strip() if title else None

        # Price by regex
        price_pattern = r'<span class="a8jt5op[^"]*"[^>]*>\s*\$([0-9]+)'
        price_match = re.search(price_pattern, html_content)
        price = f"${price_match.group(1)}" if price_match else None

        # Address by regex
        address_pattern = r'dir-ltr"><div[^>]+><section><div[^>]+ltr"><h2[^>]+>([^<]+)</h2>'
        address = re.search(address_pattern, html_content)
        address = address.group(1).strip() if address else None

        # Guests
        guest_pattern = r'<li class="l7n4lsf[^>]+>([^<]+)<span'
        guest = re.search(guest_pattern, html_content)
        guest = guest.group(1).strip() if guest else None

        # Beds & baths by Selenium (reliable!)
        beds = baths = None
        info_items = driver.find_elements(By.CSS_SELECTOR, "li.l7n4lsf")
        for item in info_items:
            text = item.text.strip().lower()
            if "bed" in text and not beds:
                beds = text
            elif "bath" in text and not baths:
                baths = text

        # Reviews
        reviews_pattern = r'<span[^>]*aria-hidden="true"[^>]*>([\d.]+)\s*·\s*(\d+)\s*reviews</span>'
        reviews_match = re.search(reviews_pattern, html_content)
        rating = reviews_match.group(1) if reviews_match else None
        total_reviews = reviews_match.group(2) if reviews_match else None

        # Host name
        host_name_pattern = r't1gpcl1t[^>]+>([^<]+)'
        host_name = re.search(host_name_pattern, html_content)
        host_name = host_name.group(1).strip() if host_name else None

        # Host info
        host_info_pattern = r'd1u64sg5[^"]+atm_67_1vlbu9m[^>]+><div><span[^>]+>([^<]+)'
        host_info = re.findall(host_info_pattern, html_content)
        host_info_list = [info.strip() for info in host_info]

        # Amenities with Selenium
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
            amenities = []

        print(f"Title: {title} | Price: {price} | Beds: {beds} | Baths: {baths}")

        return {
            "url": url,
            "Title": title,
            "Price": price,
            "Address": address,
            "Guest": guest,
            "Beds": beds,
            "Baths": baths,
            "Rating": rating,
            "Host_Name": host_name,
            "Total_Reviews": total_reviews,
            "Host_Info": host_info_list,
            "Amenities": amenities
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def save_to_csv(data, filename='airbnb_riyadh_new_data.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"✅ Data saved to {filename}")


# ----------------- Run -----------------

url = "https://www.airbnb.com/s/Al-Narjis--Riyadh-Saudi-Arabia/homes?flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2025-08-01&monthly_length=3&monthly_end_date=2025-11-01&date_picker_type=calendar&refinement_paths%5B%5D=%2Fhomes"
driver.get(url)

num_pages = 3

url_list = []

for page in range(num_pages):
    print(f"🔄 Scraping page {page + 1}...")

    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/rooms/"]'))
    )

    urls = scrape_current_page()
    url_list.extend(urls)

    print(f"Collected so far: {len(url_list)} listings")

    # Find next link href instead of clicking
    try:
        next_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[aria-label="Next"]'))
        )
        next_href = next_link.get_attribute('href')
        if not next_href:
            print("No next page link found. Done.")
            break

        driver.get(next_href)
        time.sleep(3)
    except:
        print("No more pages or next link not found.")
        break

print(f"✅ Total listings found: {len(url_list)}")

scraped_data = []

for link in url_list:
    result = scrape_details_page(link)
    if result:
        scraped_data.append(result)

if scraped_data:
    save_to_csv(scraped_data)
else:
    print("❌ No data scraped!")

driver.quit()