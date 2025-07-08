# 📊 Daily Property Crawler

This project is an **automated web scraper** that:
- ✅ Reads a list of property URLs from an **Excel input file**
- ✅ Scrapes fresh daily data (pricing, availability, reviews, amenities, etc.)
- ✅ Outputs the results as a **daily Excel snapshot**
- ✅ Runs automatically every day using **GitHub Actions**
- ✅ Uploads the output file as an **artifact** you can download anytime

---

## 🚀 **How it works**

1️⃣ **Input**  
- `properties.xlsx`  
  - Contains the list of relevant properties (Airbnb, Gathern, etc.)
  - You maintain this file — just edit, commit, and push updates.

2️⃣ **Scraper**  
- `scrape.py` loads the input file, loops through each URL, scrapes data, and stores it in a DataFrame.
- Generates a new `YYYY-MM-DD-snapshot.xlsx` in the `output/` folder.

3️⃣ **Output**  
- GitHub Actions saves the daily snapshot Excel file as an artifact attached to each workflow run.

4️⃣ **Automation**  
- `.github/workflows/scraper.yml` runs the scraper **daily at 1 AM UTC** using GitHub’s free runners.
- You can also trigger the scraper manually.

---

## 📂 **Project structure**

