# main.py

from core.tor_controller import TorController
from core.onion_scraper import OnionScraper
from core.data_manager import DataManager

def main():
    print("🕵️‍♂️ Starting Dark Web Gatherer...")

    # Start Tor service (assumes Tor is installed and available)
    tor = TorController()
    if not tor.start_tor():
        print("❌ Failed to start Tor. Exiting.")
        return

    # Initialize Onion Scraper with Tor proxy settings
    scraper = OnionScraper(proxy=tor.get_proxy())

    # List of onion URLs to scrape (in real cases, this can be from a file or crawler)
    onion_sites = [
        "http://y6xjgkgwj47us5ca.onion",
        # "http://exampleonion2.onion"
    ]

    all_data = []

    for url in onion_sites:
        print(f"🌐 Scraping: {url}")
        content = scraper.scrape_site(url)
        if content:
            all_data.append({
                "url": url,
                "content_snippet": content[:300]  # Limit for preview
            })

    # Save or display data
    data_mgr = DataManager()
    data_mgr.save_to_json(all_data, "output/onion_data.json")

    print("✅ Data gathering complete.")

if __name__ == "__main__":
    main()
