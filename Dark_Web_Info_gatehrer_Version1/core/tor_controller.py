# core/tor_controller.py

import socket
import requests

class TorController:
    def __init__(self, host='127.0.0.1', port=9050):
        self.proxy_host = host
        self.proxy_port = port

    def start_tor(self):
        print("🌀 Checking if Tor proxy is active...")
        if self._is_tor_running():
            print("✅ Tor proxy is active.")
            return True
        else:
            print("❌ Tor proxy not detected on 127.0.0.1:9050.")
            print("💡 Please start the Tor service manually (e.g., run `tor` in terminal).")
            return False

    def _is_tor_running(self):
        try:
            with socket.create_connection((self.proxy_host, self.proxy_port), timeout=5):
                return True
        except socket.error:
            return False

    def get_proxy(self):
        # Returns SOCKS5 proxy dict for requests
        return {
            "http": f"socks5h://{self.proxy_host}:{self.proxy_port}",
            "https": f"socks5h://{self.proxy_host}:{self.proxy_port}"
        }

    def test_connection(self):
        print("🌐 Testing Tor connection via check.torproject.org...")
        try:
            proxies = self.get_proxy()
            response = requests.get("https://check.torproject.org", proxies=proxies, timeout=10)
            if "Congratulations. This browser is configured to use Tor." in response.text:
                print("✅ Verified: Tor is working correctly.")
            else:
                print("⚠️ Connected, but Tor verification failed.")
        except Exception as e:
            print(f"❌ Error testing Tor connection: {e}")
