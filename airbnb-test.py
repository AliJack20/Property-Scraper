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
# options.add_argument("--headless")
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

# Function to scrape the current page and return all property URLs
def scrape_current_page():
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/rooms/"]')
    urls = []
    for link in links:
        href = link.get_attribute("href")
        if "/rooms/" in href and href not in urls:
            urls.append(href)
    return urls


# Function to scroll to the bottom of the page
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


# Function to wait for the "Next" button and click it
def go_to_next_page():
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='Next']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(1)  # Let scroll settle

        # Close any overlay/modal if present
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, '[aria-label="Close"]')
            close_button.click()
            time.sleep(1)
        except:
            pass  # Ignore if no modal

        next_button.click()
        return True
    except Exception as e:
        print(f"Couldn't navigate to next page: {e}")
        return False


# base url
url = "https://www.airbnb.com/s/Riyadh--Riyadh-Region--Saudi-Arabia/homes?flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2025-08-01&monthly_length=3&monthly_end_date=2025-11-01&place_id=ChIJbzwfOtKkLz4R5yvDtOxu8y4&refinement_paths%5B%5D=%2Fhomes&acp_id=d67b445a-d3a3-4dc9-be4f-15cc744ea123&date_picker_type=calendar&source=structured_search_input_header&search_type=unknown&query=Riyadh%2C%20Riyadh%20Region%2C%20Saudi%20Arabia&search_mode=regular_search&price_filter_input_type=2&price_filter_num_nights=5&channel=EXPLORE&checkin=2025-07-21&checkout=2025-07-25"
driver.get(url)

num_pages = 1 #int(input("How many pages do you want to scrape? "))

url_list = []

for page in range(num_pages):
    print(f"Scraping page {page + 1}...")

    # Wait for listings
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/rooms/"]'))
    )

    urls = scrape_current_page()
    for u in urls:
        print(u)
        url_list.append(u)

    if not go_to_next_page():
        break
    time.sleep(3)

print(f"Total URLs scraped: {len(url_list)}")



# function to scrape information from a details page (title, price, etc.)
def scrape_details_page(url):
    try:
        driver.get(url)
        # Wait for the page to load (you can adjust this)
        time.sleep(2)
        html_content = driver.page_source
        scroll_to_bottom_incrementally()
        time.sleep(2) 
        # Regex pattern for scraping the title
        title_pattern = r'<h1[^>]+>([^<]+)</h1>'
    
        # Scrape the title (adjust the selector according to the page structure)
        title = re.search(title_pattern,html_content)
        if title:
           title = title.group(1)
        else:
            title = None
        
        price_pattern = r'<span class="a8jt5op[^"]*"[^>]*>\s*\$([0-9]+)'
        price_match = re.search(price_pattern, html_content)

        if price_match:
            price = f"${price_match.group(1)}"
        else:
            price = None


        address_pattern = r'dir-ltr"><div[^>]+><section><div[^>]+ltr"><h2[^>]+>([^<]+)</h2>'
        address =  re.search(address_pattern,html_content)
        if address:
           address =  address.group(1)
        else:
            address = None
        
        guest_pattern = r'<li class="l7n4lsf[^>]+>([^<]+)<span'
        guest =   re.search(guest_pattern,html_content)
        if guest:
           guest = guest.group(1)
        else:
            guest = None
        # You can add more information to scrape (example: price, description, etc.)
        
        bed_bath_lis = re.findall(r'<li[^>]*class="l7n4lsf[^"]*"[^>]*>(.*?)</li>', html_content, re.DOTALL)
        bed_bath_details = []

        for item in bed_bath_lis:
            text = re.sub(r'<[^>]+>', '', item)  # Strip HTML tags
            text = text.replace("·", "").strip()
            if any(x in text.lower() for x in ["bed", "bath", "bedroom"]):
                bed_bath_details.append(text)

        
        reviews_pattern = r'<span[^>]*aria-hidden="true"[^>]*>([\d.]+)\s*·\s*(\d+)\s*reviews</span>'
        reviews_match = re.search(reviews_pattern, html_content)
        if reviews_match:
            rating = reviews_match.group(1)
            total_reviews = reviews_match.group(2)
        else:
            rating = None
            total_reviews = None



        host_name_pattern = r't1gpcl1t atm_w4_16rzvi6 atm_9s_1o8liyq atm_gi_idpfg4 dir dir-ltr[^>]+>([^<]+)'
        host_name =  re.search(host_name_pattern,html_content)
        if host_name:
           host_name = host_name.group(1)    
        else:
            host_name = None

        #total_review_pattern = r'pdp-reviews-[^>]+>[^>]+>(d+[^<]+)</span>'
        #total_review =  re.search(total_review_pattern,html_content)
        #if total_review:
        #   total_review =  total_review.group(1)    
        #else:
        #    total_review = None


        host_info_pattern = r'd1u64sg5[^"]+atm_67_1vlbu9m dir dir-ltr[^>]+><div><span[^>]+>([^<]+)'
        host_info = re.findall(host_info_pattern,html_content)
        host_info_list = []
        if host_info:
            for host_info_details in host_info:
                 host_info_list.append(host_info_details)

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



                
        # Print the scraped information (for debugging purposes)
        print(f"Title: {title}n Price:{price}n Address: {address}n Guest: {guest}n bed_bath_details:{bed_bath_details}n Ratings: {rating}n Host_name: {host_name}n total_review: {total_reviews}n Host Info: {host_info_list}n Amenities: {amenities}n" )
        
        # Return the information as a dictionary (or adjust based on your needs)
          # Store the scraped information in a dictionary
        return {
            "url": url,
            "Title": title,
            "Price": price,
            "Address": address,
            "Guest": guest,
            "Bed_Bath_Details": bed_bath_details,
            "Rating": rating,
            "Host_Name": host_name,
            "Total_Reviews": total_reviews,
            "Host_Info": host_info,
            "Amenities": amenities
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# Function to save data to CSV using pandas
def save_to_csv(data, filename='airbnb_riyadh_najris_new(1)_data.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")



scraped_data = []


# Scrape the details page for each URL stored in the url_list  
for url in url_list:
    print(f"Scraping details from: {url}")
    data = scrape_details_page(url)
    if data:
        scraped_data.append(data)
     

# After scraping, save data to CSV
if scraped_data:
    save_to_csv(scraped_data)
else:
    print("No data to save.")

# Close the browser
driver.quit()