# core/data_manager.py

import json
import os

class DataManager:
    def __init__(self):
        os.makedirs("output", exist_ok=True)  # Ensure output directory exists

    def save_to_json(self, data, filepath):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"💾 Data saved to {filepath}")
        except Exception as e:
            print(f"❌ Failed to save data: {e}")

    def load_from_json(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"❌ Failed to load data: {e}")
            return None
