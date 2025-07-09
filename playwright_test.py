from playwright.sync_api import sync_playwright

def run(playwright):
    start_url = "https://www.bhphotovideo.com/c/buy/Mirrorless-Camera-Lenses/ci/17912/N/4196380428"
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(start_url)
    page.wait_for_load_state("networkidle")

    while True:
        # ✅ Get all hrefs in one go (safe)
        hrefs = page.eval_on_selector_all(
            "a[data-selenium='miniProductPageDetailsGridViewNameLink']",
            "els => els.map(e => e.getAttribute('href'))"
        )

        product_page = browser.new_page()

        for href in hrefs:
            if href:
                url = f"https://www.bhphotovideo.com{href}"
                product_page.goto(url)
                product_page.wait_for_load_state("networkidle")

                data = product_page.locator("script[type='application/ld+json']").first.text_content()
                print(data)

        product_page.close()

        # ✅ Try to click next page
        next_button = page.locator("a[data-selenium='pagination-button-next']")
        if next_button.count() > 0 and next_button.is_enabled():
            next_button.click()
            page.wait_for_load_state("networkidle")
        else:
            break

    page.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
