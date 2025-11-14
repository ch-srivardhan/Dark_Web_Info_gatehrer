#!/usr/bin/env python3
"""
Dark Web Gatherer - Tor Controller
Manages Tor connection and ensures anonymity for dark web operations.
"""

import os
import time
import requests
from stem import Signal
from stem.control import Controller
from stem.process import launch_tor_with_config

class TorController:
    def __init__(self):
        self.tor_process = None
        self.tor_port = 9050
        self.ctrl_port = 9051
        self.proxies = {
            'http': f'socks5h://127.0.0.1:{self.tor_port}',
            'https': f'socks5h://127.0.0.1:{self.tor_port}'
        }
        self.session = self._create_session()
        self.tor_password = "DarkWebGathererSecretPassword"

    def _create_session(self):
        """Create a requests session with Tor proxies"""
        session = requests.Session()
        session.proxies = self.proxies
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        return session

    def start_tor(self):
        """Start Tor process with custom configuration"""
        if self.tor_process is not None:
            return True

        try:
            tor_config = {
                'SocksPort': str(self.tor_port),
                'ControlPort': str(self.ctrl_port),
                'HashedControlPassword': self._hash_password(),
                'ExitNodes': '{us}',
                'StrictNodes': '1',
                'MaxCircuitDirtiness': '600',
                'NewCircuitPeriod': '300',
                'CircuitBuildTimeout': '60',
                'DataDirectory': os.path.join(os.getcwd(), 'tor_data')
            }

            print("[+] Starting Tor process (this may take a while)...")
            self.tor_process = launch_tor_with_config(
                config=tor_config,
                init_msg_handler=self._tor_status
            )
            time.sleep(10)  # Wait for Tor to stabilize
            return True

        except Exception as e:
            print(f"[ERROR] Failed to start Tor: {str(e)}")
            self.stop_tor()
            return False

    def _tor_status(self, line):
        """Handler for Tor bootstrap status messages"""
        if "Bootstrapped" in line:
            print(f"[Tor] {line.split(']')[1].strip()}")

    def _hash_password(self):
        """Generate hashed password for Tor control"""
        from stem.util import term
        try:
            from stem.password import Password
            return Password.hash(self.tor_password)
        except ImportError:
            print(term.format("[!] Warning: Using default password hash", term.Color.YELLOW))
            return "16:872860B76453A77D60CA2BB8C1A7042072093276A3D701AD684053EC4C"

    def stop_tor(self):
        """Stop Tor process"""
        if self.tor_process:
            try:
                self.tor_process.terminate()
                self.tor_process.wait()
            except:
                pass
            finally:
                self.tor_process = None
        print("[+] Tor process stopped")

    def test_connection(self, timeout=30):
        """
        Verify Tor connection by checking IP address
        Returns True if connection is anonymous
        """
        test_urls = [
            'https://check.torproject.org/api/ip',
            'http://icanhazip.com'
        ]

        try:
            print("[+] Verifying Tor connection...")
            for url in test_urls:
                try:
                    response = self.session.get(url, timeout=timeout)
                    if "check.torproject.org" in url:
                        if not response.json().get('IsTor', False):
                            print("[!] Not using Tor connection")
                            return False
                    print(f"[+] Current IP: {response.text.strip()}")
                except Exception as e:
                    print(f"[!] Connection test failed ({url}): {str(e)}")
                    return False
            return True
        except Exception as e:
            print(f"[ERROR] Connection test failed: {str(e)}")
            return False

    def renew_identity(self):
        """Create new Tor circuit for a fresh identity"""
        try:
            with Controller.from_port(port=self.ctrl_port) as controller:
                controller.authenticate(password=self.tor_password)
                controller.signal(Signal.NEWNYM)
                print("[+] Tor identity renewed")
                time.sleep(5)  # Wait for circuit rebuild
                return True
        except Exception as e:
            print(f"[ERROR] Failed to renew identity: {str(e)}")
            return False

    def get_session(self):
        """Get the Tor-configured requests session"""
        return self.session