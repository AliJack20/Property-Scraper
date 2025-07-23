from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "LivedIn")]'))
        )
        print("✅ Logged in - found account button.")
        return True
    except TimeoutException:
        try:
            WebDriverWait(driver, 5).until_not(
                EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Login"]'))
            )
            print("✅ Logged in - login button disappeared.")
            return True
        except TimeoutException:
            driver.save_screenshot("login_check_failed.png")
            print("❌ Login failed - still sees login button. Screenshot saved.")
            return False

# === Scroll helper ===
def scroll_to_bottom_incrementally(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# === Scrape listings directly from cards ===
def scrape_listings_from_cards(driver):
    data_list = []
    cards = driver.find_elements(By.CSS_SELECTOR, 'article')

    for idx, card in enumerate(cards):
        data = {}

        try:
            link_elem = card.find_element(By.CSS_SELECTOR, 'a[aria-label][href*="/property/"]')
            data["URL"] = link_elem.get_attribute("href")
            data["Listing Title"] = link_elem.get_attribute("title")
        except:
            data["URL"] = None
            data["Listing Title"] = None

        try:
            data["Price"] = card.find_element(By.CSS_SELECTOR, '[aria-label="Price"]').text.strip()
        except:
            data["Price"] = None
        
        try:
            location_elem = card.find_element(By.CSS_SELECTOR, 'div[aria-label="Location"] h3')
            data["Location"] = location_elem.text.strip()
        except:
            data["Location"] = None


        try:
            data["Beds"] = card.find_element(By.CSS_SELECTOR, '[aria-label="Beds"]').text.strip()
        except:
            data["Beds"] = None

        try:
            data["Baths"] = card.find_element(By.CSS_SELECTOR, '[aria-label="Baths"]').text.strip()
        except:
            data["Baths"] = None

        try:
            data["Area"] = card.find_element(By.CSS_SELECTOR, '[aria-label="Area"]').text.strip()
        except:
            data["Area"] = None
        
        try:
            data["Residential Type"] = card.find_element(By.CSS_SELECTOR, 'span[aria-label="Type"]').text.strip()
        except:
            data["Residential Type"] = None

        # 🔍 Phone number extraction
        phone = None
        try:
            call_button = card.find_element(By.CSS_SELECTOR, 'button[aria-label="Call"]')
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", call_button)
            time.sleep(0.5)
            ActionChains(driver).move_to_element(call_button).pause(0.3).click(call_button).perform()

            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="tel:"]'))
            )
            tel_elem = driver.find_element(By.CSS_SELECTOR, 'a[href^="tel:"]')
            phone = tel_elem.get_attribute("href").replace("tel:", "").strip()

            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Close button"]')
                driver.execute_script("arguments[0].click();", close_btn)
                time.sleep(0.3)
            except:
                pass

        except Exception as e:
            print("⚠️ Phone not found:", e)

        data["Phone"] = phone

        # 🔍 Visit individual listing for extra details
        location_deed = None
        furnishing = None
        reactivated_date = None
        agency_name = None
        agent_name = None

        if data["URL"]:
            original_window = driver.current_window_handle
            driver.execute_script("window.open(arguments[0]);", data["URL"])
            driver.switch_to.window(driver.window_handles[-1])

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span._5746987e'))
                )

                # Location Deed
                label_elements = driver.find_elements(By.CSS_SELECTOR, 'span._3a13c305')
                for label in label_elements:
                    if "Location Description as per Deed:" in label.text:
                        deed_elem = label.find_element(By.CSS_SELECTOR, 'span._78a722b5')
                        location_deed = deed_elem.text.strip()
                        break

                # Furnishing
                try:
                    furnishing = driver.find_element(By.XPATH, '//li[span[text()="Furnishing"]]/span[@aria-label="Furnishing"]').text.strip()
                except:
                    furnishing = None

                # Reactivated Date
                try:
                    reactivated_date = driver.find_element(By.XPATH, '//li[span[text()="Added on"]]/span[@aria-label="Reactivated date"]').text.strip()
                except:
                    reactivated_date = None

                # Agency Name
                try:
                    agency_elem = driver.find_element(By.CSS_SELECTOR, 'span[aria-label="Agency name"]')
                    agency_name = agency_elem.text.strip()
                except:
                    agency_name = None

                # Agent Name
                try:
                    agent_elem = driver.find_element(By.CSS_SELECTOR, 'span[aria-label="Agent name"]')
                    agent_name = agent_elem.text.strip()
                except:
                    agent_name = None
                
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

            except Exception as e:
                print(f"⚠️ Details not found for {data['URL']}: {e}")

            

            driver.close()
            driver.switch_to.window(original_window)

        data["Deed Location"] = location_deed
        data["Furnishing"] = furnishing
        data["Reactivated Date"] = reactivated_date
        data["Agency Name"] = agency_name
        data["Agent Name"] = agent_name

        print(f"[{idx+1}] ✅ Collected:", data)
        data_list.append(data)

    return data_list



# === Main Execution ===
EMAIL = 'support@livedin.co'
PASSWORD = 'Livedin2025!'
base_url = "https://www.bayut.sa/en/to-rent/properties/riyadh/"

driver = create_driver()
driver.get(base_url)

if not login(driver, EMAIL, PASSWORD):
    print("❌ Login failed. Exiting.")
    driver.quit()
    exit()

# === Scrape paginated results ===
all_data = []
num_pages = 288
for page in range(1, num_pages + 1):
    url = base_url if page == 1 else f"{base_url}&page={page}"
    print(f"\n📄 Scraping page {page}: {url}")
    driver.get(url)
    time.sleep(3)
    scroll_to_bottom_incrementally(driver)
    listings = scrape_listings_from_cards(driver)
    all_data.extend(listings)

driver.quit()
df = pd.DataFrame(all_data)
df.to_excel("bayut_final_properties.xlsx", index=False)
print("✅ Saved to bayut_final_properties.xlsx")