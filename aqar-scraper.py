from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time


options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless")  # Uncomment for headless mode

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)


base_url = "https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%B4%D9%85%D8%A7%D9%84-%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6/%D8%AD%D9%8A-%D8%A7%D9%84%D9%86%D8%B1%D8%AC%D8%B3?beds=eq,3&rent_period=eq,3"
all_links = []

num_pages = 3  # Pages to scrape

# -------------------------------
# ✅ 3️⃣ Helper to scroll fully
# -------------------------------
def scroll_to_bottom():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


for page in range(1, num_pages + 1):
    url = f"{base_url}{page}"
    driver.get(url)
    print(f"🔵 Scraping page: {url}")

    scroll_to_bottom()

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '//a[contains(@href, "/أراضي-للبيع/")]')
            )
        )
    except:
        print(f"⚠️ No listings found on page {page}")
        continue

    offers = driver.find_elements(
        By.XPATH, '//a[contains(@href, "/أراضي-للبيع/")]'
    )

    page_links = []
    for offer in offers:
        href = offer.get_attribute("href")
        if href and "/أراضي-للبيع/" in href:
            if href.startswith("http"):
                full_url = href
            else:
                full_url = f"https://sa.aqar.fm{href}"
            if full_url not in all_links:
                page_links.append(full_url)

    print(f"✅ Found {len(page_links)} listings on page {page}")
    all_links.extend(page_links)

print(f"🟢 Total unique listings: {len(all_links)}")


main_location = []
sub_location = []
hood = []
size = []
pricepm = []
frontage = []
purpose = []
street_width = []

for idx, link in enumerate(all_links):
    driver.get(link)
    print(f"🔵 ({idx + 1}/{len(all_links)}) {link}")
    time.sleep(2)

    try:
        tree = driver.find_elements(By.CSS_SELECTOR, 'a.treeLink')
        if len(tree) > 3:
            main_location.append(tree[1].text.strip())
            sub_location.append(tree[2].text.strip())
            hood.append(tree[3].text.strip())
        else:
            main_location.append(tree[1].text.strip())
            sub_location.append(None)
            hood.append(tree[2].text.strip())
    except:
        main_location.append(None)
        sub_location.append(None)
        hood.append(None)

    try:
        table = driver.find_elements(By.CSS_SELECTOR, 'td[align="right"][dir="rtl"]')
        size.append(table[0].text.strip() if len(table) > 0 else None)
        pricepm.append(table[2].text.strip() if len(table) > 2 else None)
        frontage.append(table[4].text.strip() if len(table) > 4 else None)
        purpose.append(table[6].text.strip() if len(table) > 6 else None)
        street_width.append(table[8].text.strip() if len(table) > 8 else None)
    except:
        size.append(None)
        pricepm.append(None)
        frontage.append(None)
        purpose.append(None)
        street_width.append(None)


df = pd.DataFrame({
    "main_location": main_location,
    "sub_location": sub_location,
    "hood": hood,
    "size": size,
    "price_per_meter": pricepm,
    "frontage": frontage,
    "purpose": purpose,
    "street_width": street_width
})

df.to_csv("aqar_land_data_fixed.csv", index=False)
print("🟢 Saved to aqar_land_data_fixed.csv")

# -------------------------------
# ✅ 7️⃣ Done
# -------------------------------
driver.quit()
