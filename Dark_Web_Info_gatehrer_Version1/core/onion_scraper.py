# core/onion_scraper.py

import requests

class OnionScraper:
    def __init__(self, proxy):
        self.proxies = proxy
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def scrape_site(self, url):
        try:
            response = requests.get(
                url,
                proxies=self.proxies,
                headers=self.headers,
                timeout=15
            )
            if response.status_code == 200:
                print("📄 Page fetched successfully.")
                return response.text
            else:
                print(f"⚠️ Failed to fetch page. Status code: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"❌ Error scraping site: {e}")
            return None
