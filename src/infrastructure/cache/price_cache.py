# src/infrastructure/cache/price_cache.py

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict


class PriceCache:
    """Simple price caching to reduce API calls."""

    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "price_cache.json"
        self.cache_duration = timedelta(minutes=5)  # Cache prices for 5 minutes
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def get_price(self, symbol: str) -> Optional[float]:
        """Get cached price if available and not expired."""
        if symbol in self.cache:
            cached_data = self.cache[symbol]
            cached_time = datetime.fromisoformat(cached_data['timestamp'])

            if datetime.now() - cached_time < self.cache_duration:
                return cached_data['price']

        return None

    def set_price(self, symbol: str, price: float):
        """Cache a price."""
        self.cache[symbol] = {
            'price': price,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()

    def clear_cache(self):
        """Clear all cached prices."""
        self.cache = {}
        self._save_cache()
