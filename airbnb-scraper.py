from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import re
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options)

# Stealth setup to avoid detection
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

# 🔍 Extracts both URL and card location from listing cards
def scrape_card_location_from_card_elements():
    cards = driver.find_elements(By.CSS_SELECTOR, 'div[itemprop="itemListElement"]')
    card_info = []
    seen = set()

    for card in cards:
        try:
            url = card.find_element(By.TAG_NAME, 'a').get_attribute("href")
            location = ""
            try:
                location_elem = card.find_element(By.CSS_SELECTOR, 'div[class*="t1jojoys"]')
                location = location_elem.text.strip()
            except NoSuchElementException:
                pass

            if url not in seen:
                card_info.append((url, location))
                seen.add(url)
        except Exception as e:
            print("Card parse error:", e)

    return card_info

# ⬇️ Scroll
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

# ➡️ Pagination
def go_to_next_page():
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='Next']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(1)

        try:
            close_button = driver.find_element(By.CSS_SELECTOR, '[aria-label="Close"]')
            close_button.click()
            time.sleep(1)
        except:
            pass

        next_button.click()
        return True
    except Exception as e:
        print(f"Couldn't navigate to next page: {e}")
        return False


# ⬅️ Collect URLs & card locations
url = "https://www.airbnb.com/s/Riyadh--Riyadh-Region--Saudi-Arabia/homes?refinement_paths%5B%5D=%2Fhomes&acp_id=d67b445a-d3a3-4dc9-be4f-15cc744ea123&date_picker_type=calendar&source=structured_search_input_header&search_type=autocomplete_click&flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2025-08-01&monthly_length=3&monthly_end_date=2025-11-01&search_mode=regular_search&price_filter_input_type=2&channel=EXPLORE&checkin=2025-08-01&checkout=2025-08-02&price_filter_num_nights=1&zoom_level=9&query=Riyadh%2C%20Riyadh%20Region%2C%20Saudi%20Arabia&place_id=ChIJbzwfOtKkLz4R5yvDtOxu8y4&pagination_search=true&federated_search_session_id=72f3409d-d227-43dd-a6b1-b8cdd72c3725&cursor=eyJzZWN0aW9uX29mZnNldCI6MCwiaXRlbXNfb2Zmc2V0IjowLCJ2ZXJzaW9uIjoxfQ%3D%3D"
driver.get(url)
time.sleep(3)

num_pages = 15  # adjust as needed
url_list = []

for page in range(num_pages):
    print(f"Scraping page {page + 1}...")

    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/rooms/"]'))
    )

    cards = scrape_card_location_from_card_elements()
    for u, loc in cards:
        print(f"{u} | {loc}")
        url_list.append((u, loc))

    if not go_to_next_page():
        break
    time.sleep(3)

print(f"Total URLs scraped: {len(url_list)}")

# 🏠 Scrape individual listing
def scrape_details_page(url, card_location):
    try:
        driver.get(url)
        time.sleep(2)
        html_content = driver.page_source
        scroll_to_bottom_incrementally()
        time.sleep(2)

        title = re.search(r'<h1[^>]+>([^<]+)</h1>', html_content)
        title = title.group(1) if title else None

        price_match = re.search(r'<span class="a8jt5op[^"]*"[^>]*>\s*\$([0-9]+)', html_content)
        price = f"${price_match.group(1)}" if price_match else None

        address_match = re.search(r'dir-ltr"><div[^>]+><section><div[^>]+ltr"><h2[^>]+>([^<]+)</h2>', html_content)
        address = address_match.group(1) if address_match else None

        guest_match = re.search(r'<li class="l7n4lsf[^>]+>([^<]+)<span', html_content)
        guest = guest_match.group(1) if guest_match else None

        bed_bath_lis = re.findall(r'<li[^>]*class="l7n4lsf[^"]*"[^>]*>(.*?)</li>', html_content, re.DOTALL)
        bed_bath_details = [re.sub(r'<[^>]+>', '', item).replace("·", "").strip()
                            for item in bed_bath_lis
                            if any(x in item.lower() for x in ["bed", "bath", "bedroom"])]

        reviews_match = re.search(r'<span[^>]*aria-hidden="true"[^>]*>([\d.]+)\s*·\s*(\d+)\s*reviews</span>', html_content)
        rating = reviews_match.group(1) if reviews_match else None
        total_reviews = reviews_match.group(2) if reviews_match else None

        host_name_match = re.search(r't1gpcl1t atm_w4_16rzvi6 atm_9s_1o8liyq atm_gi_idpfg4 dir dir-ltr[^>]+>([^<]+)', html_content)
        host_name = host_name_match.group(1) if host_name_match else None

        host_info_pattern = r'd1u64sg5[^"]+atm_67_1vlbu9m dir dir-ltr[^>]+><div><span[^>]+>([^<]+)'
        host_info = re.findall(host_info_pattern, html_content)

        # Amenities from popup
        try:
            # Click the "Show all amenities" button (span)
            show_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//span[contains(text(), "Show all") and contains(text(), "amenities")]')
                )
            )
            driver.execute_script("arguments[0].click();", show_btn)
            time.sleep(1)

            # Wait for modal to appear
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="dialog"]'))
            )
            time.sleep(0.5)

            # Now fetch amenities in modal
            amenity_elements = driver.find_elements(
                By.XPATH, '//div[contains(@id, "row-title") and contains(@class, "atm_7l_jt7fhx")]'
            )
            amenities = [el.text.strip() for el in amenity_elements if el.text.strip()]

            # Close the modal
            try:
                close_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@role="dialog"]//button[@aria-label="Close"]'))
                )
                driver.execute_script("arguments[0].click();", close_btn)
                time.sleep(1)
            except Exception as close_e:
                print("⚠️ Modal close failed:", close_e)

        except Exception as e:
            print("❌ Amenities error:", e)
            amenities = []


        return {
            "URL": url,
            "Card_Location": card_location,
            "Title": title,
            "Price": price,
            "Address": address,
            "Guest": guest,
            "Bed_Bath_Details": bed_bath_details,
            "Rating": rating,
            "Total_Reviews": total_reviews,
            "Host_Name": host_name,
            "Host_Info": host_info,
            "Amenities": amenities
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def save_to_csv(data, filename='airbnb_riyadh_data.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"✅ Data saved to {filename}")

# 🔁 Scrape each URL
scraped_data = []
for url, card_location in url_list:
    print(f"Scraping details from: {url}")
    data = scrape_details_page(url, card_location)
    if data:
        scraped_data.append(data)
        print(data)

if scraped_data:
    save_to_csv(scraped_data)
else:
    print("No data to save.")

driver.quit()
