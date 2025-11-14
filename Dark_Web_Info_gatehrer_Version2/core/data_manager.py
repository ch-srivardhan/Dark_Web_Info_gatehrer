#!/usr/bin/env python3
"""
Dark Web Gatherer - Data Manager
Secure storage and handling of collected dark web data with encryption.
"""

import os
import json
import sqlite3
from datetime import datetime
import hashlib
from cryptography.fernet import Fernet
import logging

class DataManager:
    def __init__(self, db_name="darkweb_data.db"):
        self.db_name = db_name
        self.key_file = "data_key.key"
        self.cipher = self._init_crypto()
        self.logger = self._init_logging()
        self._init_db()

    def _init_logging(self):
        """Initialize secure logging"""
        logger = logging.getLogger('DarkWebDataManager')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('darkweb_gatherer.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
        
        return logger

    def _init_crypto(self):
        """Initialize encryption system"""
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        
        with open(self.key_file, 'rb') as f:
            key = f.read()
        
        return Fernet(key)

    def _init_db(self):
        """Initialize secure database"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Main data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collected_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    content BLOB,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source_hash TEXT UNIQUE,
                    is_sensitive INTEGER DEFAULT 0
                )
            ''')
            
            # Metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_start DATETIME,
                    scan_end DATETIME,
                    items_collected INTEGER,
                    domains_scanned TEXT
                )
            ''')
            
            conn.commit()

    def _encrypt_data(self, data):
        """Encrypt sensitive data before storage"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)

    def _decrypt_data(self, encrypted_data):
        """Decrypt stored data"""
        return self.cipher.decrypt(encrypted_data).decode()

    def save(self, items):
        """Save collected items to secure database"""
        if not items:
            return False

        scan_start = datetime.now()
        domains = set()
        saved_count = 0

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            for item in items:
                try:
                    # Generate content hash for deduplication
                    content_hash = hashlib.sha256(
                        (item.get('url', '') + str(item.get('content', ''))).encode()
                    ).hexdigest()
                    
                    # Encrypt sensitive content
                    encrypted_content = self._encrypt_data(
                        json.dumps(item.get('content', ''))
                    ) if item.get('content') else None
                    
                    # Extract domain
                    domain = item['url'].split('/')[2] if 'url' in item else 'unknown'
                    domains.add(domain)
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO collected_data (
                            data_type, title, url, content, source_hash
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        item.get('type', 'unknown'),
                        item.get('title', 'No title')[:500],  # Truncate long titles
                        item['url'],
                        encrypted_content,
                        content_hash
                    ))
                    
                    saved_count += cursor.rowcount
                    
                except Exception as e:
                    self.logger.error(f"Failed to save item {item.get('url')}: {str(e)}")
                    continue

            # Record scan metadata
            cursor.execute('''
                INSERT INTO scan_metadata (
                    scan_start, items_collected, domains_scanned
                ) VALUES (?, ?, ?)
            ''', (
                scan_start,
                saved_count,
                ','.join(list(domains)[:10])  # Store first 10 domains
            ))
            
            conn.commit()

        self.logger.info(f"Saved {saved_count}/{len(items)} items from {len(domains)} domains")
        return saved_count > 0

    def load(self, limit=100, decrypt_content=True):
        """Load collected data with optional decryption"""
        results = []
        
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM collected_data
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            for row in cursor.fetchall():
                item = dict(row)
                
                if decrypt_content and item['content']:
                    try:
                        item['content'] = json.loads(
                            self._decrypt_data(item['content'])
                        )
                    except:
                        item['content'] = "[ENCRYPTED CONTENT]"
                
                results.append(item)
        
        return results

    def get_stats(self):
        """Get collection statistics"""
        stats = {
            'total': 0,
            'domains': 0,
            'last_updated': 'Never'
        }
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Get total items
            cursor.execute('SELECT COUNT(*) FROM collected_data')
            stats['total'] = cursor.fetchone()[0]
            
            # Get unique domains
            cursor.execute('''
                SELECT COUNT(DISTINCT substr(url, 0, instr(substr(url, 9), '/'))
                FROM collected_data
            ''')
            stats['domains'] = cursor.fetchone()[0]
            
            # Get last update time
            cursor.execute('''
                SELECT MAX(timestamp) FROM collected_data
            ''')
            last_update = cursor.fetchone()[0]
            if last_update:
                stats['last_updated'] = last_update
        
        return stats

    def export(self, output_file, format='json'):
        """Export data securely"""
        data = self.load(decrypt_content=True)
        
        if format.lower() == 'json':
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Exported {len(data)} items to {output_file}")
            return True
        
        elif format.lower() == 'csv':
            import csv
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            self.logger.info(f"Exported {len(data)} items to {output_file}")
            return True
        
        return False

    def wipe(self):
        """Securely wipe sensitive data"""
        try:
            if os.path.exists(self.db_name):
                # Overwrite file before deletion (basic sanitization)
                with open(self.db_name, 'wb') as f:
                    f.write(os.urandom(os.path.getsize(self.db_name)))
                os.remove(self.db_name)
                
            if os.path.exists(self.key_file):
                os.remove(self.key_file)
                
            self.logger.warning("All data was securely wiped")
            return True
        except Exception as e:
            self.logger.error(f"Wipe failed: {str(e)}")
            return False