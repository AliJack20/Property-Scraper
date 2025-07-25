from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

# === Setup Chrome ===
options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options=options)

stealth(driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

num_pages = 2  


# === Visit Gathern Search Page ===
urls = []
base_url = "https://gathern.co/en/search?chalet_cats=6%2C7%2C8%2C9&city=3"

for page in range(1, num_pages + 1):
    url = f"{base_url}&page={page}"
    print(f"🌐 Visiting page {page}: {url}")
    driver.get(url)
    
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.e1aemmpj2")))
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, "a.e1aemmpj2")
        page_urls = [card.get_attribute("href") for card in cards if card.get_attribute("href")]
        print(f"✅ Page {page}: Found {len(page_urls)} listings")
        urls.extend(page_urls)
    except Exception as e:
        print(f"⚠️ Error loading page {page}: {e}")
        continue

results = []

# === Visit Each Listing ===
for index, link in enumerate(urls):
    try:
        print(f"🔍 Scraping {index+1}/{len(urls)}: {link}")
        driver.get(link)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(2)

        # Use BeautifulSoup to get full page HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        try:
            title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            title = ""

        try:
            location = driver.find_element(By.CSS_SELECTOR, "span.e151t6uh7").text.strip()
        except:
            location = ""

        try:
            # Find all spans with this class
            spans = driver.find_elements(By.CSS_SELECTOR, "span.ltr-1h8u2rk.e151t6uh7")
            area = ""
            for span in spans:
                if "Unit Area" in span.text:
                    match = re.search(r'(\d+)', span.text)
                    if match:
                        area = match.group(1)
                        break
        except:
            area = ""


        try:
            rating_block = driver.find_element(By.CSS_SELECTOR, "span.ltr-1u44dny.e151t6uh8")
            rating_text = rating_block.text.strip()
            
            # Rating is the first part (before space), reviews in parentheses
            rating = rating_text.split()[0]  # "10"
            reviews = rating_text.split("(")[1].split()[0]  # "34"
        except:
            rating = ""
            reviews = ""


        try:
            price_per_night = driver.find_element(By.CSS_SELECTOR, "b.ltr-437vva").text.strip()
        except:
            price_per_night = ""


        #try:
            #total_price_element = driver.find_element(By.XPATH, "//p[contains(@class, 'MuiTypography-body1') and contains(text(), 'Saudi Riyal')]")
            #total_price = total_price_element.text.strip().split()[0]  # Get only the numeric part
        #except:
            #total_price = ""

        try:
            beds = ""
            baths = ""
            items = driver.find_elements(By.CSS_SELECTOR, "ul.ltr-1gtoalg.e1hx4far2 li")
            for item in items:
                text = item.text.strip()
                if "Bedrooms" in text:
                    beds = text
                elif "Bathrooms" in text:
                    baths = text
        except:
            beds = ""
            baths = ""

        try:
            amenities_list = driver.find_elements(By.CSS_SELECTOR, 'ul.ltr-1gtoalg.e1hx4far2 li')
            amenities = [amenity.text.strip() for amenity in amenities_list if amenity.text.strip()]
            amenities_str = ', '.join(amenities)
        except:
            amenities_str = ''



        results.append({
            "URL": link,
            "Title": title,
            "Location": location,
            "Area sq/m": area,
            "PricePerNight": price_per_night,
            #"TotalPrice": total_price,
            "Rating": rating,
            "Reviews": reviews,
            "Beds": beds,
            "Baths": baths,
            'Amenities': amenities_str
        })
        #print(results)

    except Exception as e:
        print(f"⚠️ Error scraping {link}: {e}")
        continue

driver.quit()

# === Save to Excel ===
df = pd.DataFrame(results)
df.to_excel("gathern_detailed.xlsx", index=False)
print("✅ Saved to gathern_detailed.xlsx")
