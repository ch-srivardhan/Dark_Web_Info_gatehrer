#!/usr/bin/env python3
"""
Dark Web Gatherer - Main Module
Entry point for dark web data collection system.
Handles Tor connection, site scraping, and data storage.
"""

import time
from core.tor_controller import TorController
from core.onion_scraper import OnionScraper
from core.data_manager import DataManager

class DarkWebGatherer:
    def __init__(self):
        self.tor = TorController()
        self.scraper = OnionScraper()
        self.data_manager = DataManager()
        self.running = False

    def start(self):
        """Start the dark web gathering process"""
        print("\n=== Dark Web Gatherer ===")
        print("[!] This tool should only be used for legal research purposes\n")

        try:
            # Initialize components
            print("[+] Initializing Tor connection...")
            self.tor.start_tor()
            
            print("[+] Testing Tor connectivity...")
            if not self.tor.test_connection():
                raise RuntimeError("Tor connection failed")

            # Main loop
            self.running = True
            while self.running:
                try:
                    print("\n[1] Scrape specific onion site")
                    print("[2] Search hidden services")
                    print("[3] View collected data")
                    print("[4] Exit")
                    
                    choice = input("\nSelect option: ").strip()
                    
                    if choice == "1":
                        self._scrape_site()
                    elif choice == "2":
                        self._search_services()
                    elif choice == "3":
                        self._view_data()
                    elif choice == "4":
                        self.running = False
                    else:
                        print("[!] Invalid option")
                
                except KeyboardInterrupt:
                    print("\n[!] Received interrupt signal")
                    self.running = False
                except Exception as e:
                    print(f"[ERROR] Operation failed: {str(e)}")
                    time.sleep(2)

        finally:
            # Cleanup
            print("\n[+] Shutting down...")
            self.tor.stop_tor()
            print("[+] Done")

    def _scrape_site(self):
        """Handle single site scraping"""
        onion_url = input("Enter onion URL (including .onion): ").strip()
        if not onion_url.endswith('.onion'):
            print("[!] Invalid onion address")
            return
        
        depth = input("Crawl depth (1-3): ").strip()
        try:
            depth = min(max(int(depth), 1), 3)
        except ValueError:
            depth = 1

        print(f"\n[+] Scraping {onion_url} (depth: {depth})...")
        results = self.scraper.scrape(onion_url, depth)
        self.data_manager.save(results)
        print(f"[+] Saved {len(results)} items")

    def _search_services(self):
        """Search across multiple hidden services"""
        query = input("Enter search query: ").strip()
        if not query:
            print("[!] Query cannot be empty")
            return

        max_results = input("Max results to collect (10-100): ").strip()
        try:
            max_results = min(max(int(max_results), 10), 100)
        except ValueError:
            max_results = 25

        print(f"\n[+] Searching for '{query}' (max: {max_results})...")
        results = self.scraper.search(query, max_results)
        self.data_manager.save(results)
        print(f"[+] Saved {len(results)} results")

    def _view_data(self):
        """View collected data"""
        print("\n[+] Collected data summary:")
        stats = self.data_manager.get_stats()
        print(f"- Total entries: {stats['total']}")
        print(f"- Unique domains: {stats['domains']}")
        print(f"- Last updated: {stats['last_updated']}")

        if input("\nView details? (y/n): ").lower() == 'y':
            for entry in self.data_manager.load():
                print(f"\n[+] {entry['type'].upper()}: {entry['title']}")
                print(f"URL: {entry['url']}")
                print(f"Found: {entry['timestamp']}")

if __name__ == "__main__":
    gatherer = DarkWebGatherer()
    gatherer.start()