import requests
from bs4 import BeautifulSoup

url = "https://www.airbnb.com/rooms/1041391936532027692"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

title = soup.find("title")
print("Title:", title.text.strip())

# Try finding description
description = soup.find("meta", {"name": "description"})
if description:
    print("Description:", description['content'])
else:
    print("Description: Not found")
