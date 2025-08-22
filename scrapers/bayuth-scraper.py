from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import pandas as pd

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

# === Extract Listing Age from a single URL ===
# === Extract Listing Age from a single URL ===
def get_listing_age(driver, url):
    driver.get(url)
    try:
        # wait for details section to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.f1a238ef"))
        )

        # 🔘 Click "See More" button if present
        try:
            see_more_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[@role="button" and contains(@aria-label,"View More")]')
                )
            )
            driver.execute_script("arguments[0].click();", see_more_btn)
            time.sleep(1)  # small pause to let content load
        except TimeoutException:
            print("No see more button")
            pass  # no see more button

        # ✅ Extract Listing Age
        try:
            age_elem = driver.find_element(
                By.XPATH,
                '//li[span[@class="c3afaaa3" and normalize-space(text())="Listing Age"]]/span[@class="_9a7b7a70"]'
            )
            return age_elem.text.strip()
        except NoSuchElementException:
            return None

    except TimeoutException:
        return None


# === Main Execution ===
INPUT_CSV = "Market Analysis - Lease Data.csv"     # your file with URLs
OUTPUT_CSV = "bayut_final_properties.xlsx"   # file with Listing Age added

df = pd.read_csv(INPUT_CSV)
df = df.head(20)

driver = create_driver()

listing_ages = []
for idx, row in df.iterrows():
    url = row["URL"]  # assumes your CSV column is named "URL"
    print(f"[{idx+1}] Visiting {url}")
    age = get_listing_age(driver, url)
    listing_ages.append(age)
    print(f"    → Listing Age: {age}")

driver.quit()

# add new column to dataframe
df["Listing Age"] = listing_ages

# save updated CSV
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Done! Results saved to {OUTPUT_CSV}")
