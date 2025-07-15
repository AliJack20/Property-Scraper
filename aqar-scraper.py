from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import re
import time


options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless")  # Optional

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

base_url = "https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%B4%D9%85%D8%A7%D9%84-%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%AD%D9%8A-%D8%A7%D9%84%D9%86%D8%B1%D8%AC%D8%B3?rent_period=eq,3&beds=eq,3"

num_pages = 3  # set pages you want

urls, prices, bedrooms, bathrooms, areas = [], [], [], [], []


for page in range(1, num_pages + 1):
    if page == 1:
        url = base_url
    else:
        url = f"{base_url}/{page}"

    print(f"Scraping page: {url}")
    driver.get(url)

    # Let content load + scroll
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Wait for listings
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div._listingCard__PoR_B'))
        )
    except:
        print(f"No listings found on page {page}")
        continue

    cards = driver.find_elements(By.CSS_SELECTOR, 'div._listingCard__PoR_B')
    print(f"Found {len(cards)} cards on page {page}")

    for card in cards:
        # ✅ Get the parent <a> tag for URL
        try:
            parent_a = card.find_element(By.XPATH, "./ancestor::a[1]")
            href = parent_a.get_attribute("href")
            if href.startswith("/"):
                href = "https://sa.aqar.fm" + href
        except:
            href = None

        # ✅ Price clean
        try:
            raw_price = card.find_element(By.CSS_SELECTOR, 'p._price__X51mi span').text.strip()
            clean_price = re.findall(r'[\d,]+', raw_price)
            price = clean_price[0] if clean_price else None
        except:
            price = None

        # ✅ Specs
        specs = card.find_elements(By.CSS_SELECTOR, 'div._specs__nbsgm div._spec__SIJiK')

        bed = bath = area = None

        for spec in specs:
            try:
                icon = spec.find_element(By.TAG_NAME, 'img').get_attribute('alt')
                value = spec.text.strip()

                if 'الغرف' in icon or 'bed' in icon or 'عدد الغرف' in icon:
                    bed = re.sub(r'\D', '', value)
                elif 'الحمامات' in icon or 'bath' in icon or 'عدد الحمامات' in icon:
                    bath = re.sub(r'\D', '', value)
                elif 'المساحة' in icon or 'area' in icon:
                    area_match = re.findall(r'\d+', value.replace('\xa0', ''))
                    area = area_match[0] if area_match else None
            except:
                continue

        urls.append(href)
        prices.append(price)
        bedrooms.append(bed)
        bathrooms.append(bath)
        areas.append(area)

# -------------------------------
# ✅ Save results
# -------------------------------
df = pd.DataFrame({
    "URL": urls,
    "Price": prices,
    "Bedrooms": bedrooms,
    "Bathrooms": bathrooms,
    "Area": areas
})

df.to_csv("aqar_all_pages.csv", index=False)
print("✅ Saved to aqar_all_pages.csv")

driver.quit()
