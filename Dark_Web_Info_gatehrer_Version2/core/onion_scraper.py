#!/usr/bin/env python3
"""
Dark Web Gatherer - Onion Scraper
Specialized web scraper for .onion sites with Tor anonymity.
"""

import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
import re

class OnionScraper:
    def __init__(self):
        self.visited_urls = set()
        self.ua = UserAgent()
        self.max_retries = 3
        self.timeout = 30
        self.request_delay = (3, 7)  # Random delay between requests
        self.blacklist = [
            r"\.exe$", r"\.zip$", r"\.rar$", r"\.tar$", r"\.gz$",
            r"\.mp3$", r"\.mp4$", r"\.avi$", r"\.mkv$", r"\.pdf$"
        ]

    def scrape(self, onion_url, depth=1):
        """
        Scrape an onion site with specified depth
        Returns list of discovered items
        """
        if not self._validate_onion_url(onion_url):
            raise ValueError("Invalid .onion URL")

        results = []
        self.visited_urls.clear()
        
        try:
            self._crawl(onion_url, depth, results)
        except Exception as e:
            print(f"[!] Scraping interrupted: {str(e)}")
        
        return results

    def search(self, query, max_results=25):
        """
        Search across multiple hidden services
        Returns list of relevant items
        """
        # Implement dark web search logic
        # This is a placeholder - actual implementation would require
        # integration with dark web search engines or directories
        print(f"[!] Dark web search not fully implemented (demo mode)")
        
        # Simulate finding results
        simulated_results = []
        for i in range(min(max_results, 5)):  # Demo: max 5 results
            simulated_results.append({
                'type': 'search_result',
                'title': f"Result for '{query}' #{i+1}",
                'url': f"http://simulated{random.randint(1,100)}.onion",
                'content': f"Sample content containing {query}",
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return simulated_results

    def _crawl(self, url, depth, results, current_depth=0):
        """Recursive crawling function with depth control"""
        if current_depth > depth or url in self.visited_urls:
            return

        self.visited_urls.add(url)
        print(f"[+] Crawling: {url} (depth {current_depth})")

        try:
            html_content = self._fetch_url(url)
            if not html_content:
                return

            # Extract page information
            page_data = self._extract_page_data(url, html_content)
            if page_data:
                results.append(page_data)

            # Extract and follow links if not at max depth
            if current_depth < depth:
                for link in self._extract_links(url, html_content):
                    time.sleep(random.uniform(*self.request_delay))
                    self._crawl(link, depth, results, current_depth + 1)

        except Exception as e:
            print(f"[!] Failed to crawl {url}: {str(e)}")

    def _fetch_url(self, url):
        """Fetch URL content with retries and random delays"""
        from core.tor_controller import TorController
        tor = TorController()
        session = tor.get_session()

        for attempt in range(self.max_retries):
            try:
                # Rotate user agent and add random delay
                session.headers.update({'User-Agent': self.ua.random})
                time.sleep(random.uniform(*self.request_delay))

                response = session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=False
                )

                if response.status_code == 200:
                    return response.text
                elif response.status_code in (403, 404):
                    return None
                else:
                    print(f"[!] HTTP {response.status_code} at {url}")
                    return None

            except Exception as e:
                print(f"[!] Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(5)
                tor.renew_identity()

        return None

    def _extract_page_data(self, url, html):
        """Extract structured data from page HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style", "iframe", "noscript"]):
            script.decompose()

        title = soup.title.string if soup.title else url
        text = ' '.join(soup.stripped_strings)
        
        return {
            'type': 'page',
            'title': title[:200],  # Limit title length
            'url': url,
            'content': text[:5000],  # Limit content size
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'links': len(soup.find_all('a'))
        }

    def _extract_links(self, base_url, html):
        """Extract and validate links from page content"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()

        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith(('javascript:', 'mailto:', '#')):
                continue

            # Join relative URLs and filter
            full_url = urljoin(base_url, href)
            if (self._validate_onion_url(full_url) and 
                not self._is_blacklisted(full_url)):
                links.add(full_url)

        return list(links)[:20]  # Limit number of followed links

    def _validate_onion_url(self, url):
        """Validate that URL is a proper .onion address"""
        try:
            parsed = urlparse(url)
            return (parsed.scheme in ('http', 'https') and 
                    parsed.netloc.endswith('.onion') and
                    len(parsed.netloc) == 22)  # Standard v2 onion address
        except:
            return False

    def _is_blacklisted(self, url):
        """Check if URL matches any blacklist pattern"""
        return any(re.search(pattern, url.lower()) for pattern in self.blacklist)