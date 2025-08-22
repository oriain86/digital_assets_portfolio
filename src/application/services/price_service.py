# src/application/services/price_service.py

import requests
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime
import time


class PriceService:
    """Service for fetching cryptocurrency prices."""

    def __init__(self):
        # Using CoinGecko API (free tier)
        self.base_url = "https://api.coingecko.com/api/v3"
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network',
            'LUNA': 'terra-luna',
            'FTM': 'fantom',
            'ONE': 'harmony',
            'NEAR': 'near',
            'HNT': 'helium',
            'AXS': 'axie-infinity',
            'SAND': 'the-sandbox',
            'FET': 'fetch-ai',
            'EGLD': 'elrond-erd-2',
            'SUI': 'sui',
            'VIRTUAL': 'virtual-protocol',
            # Add more mappings as needed
        }
        self.last_request_time = 0
        self.min_request_interval = 1.2  # Rate limit: 50 calls/minute

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a single asset."""
        # Handle stablecoins
        if symbol in ['USD', 'USDC', 'USDT', 'DAI', 'BUSD']:
            return 1.0

        coin_id = self.symbol_to_id.get(symbol)
        if not coin_id:
            print(f"Unknown symbol: {symbol}")
            return None

        # Rate limiting
        self._rate_limit()

        try:
            response = requests.get(
                f"{self.base_url}/simple/price",
                params={
                    'ids': coin_id,
                    'vs_currencies': 'usd'
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get(coin_id, {}).get('usd')
            else:
                print(f"API error for {symbol}: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None

    def get_multiple_prices(self, symbols: list) -> Dict[str, float]:
        """Get current prices for multiple assets."""
        prices = {}

        # Handle stablecoins
        for symbol in symbols:
            if symbol in ['USD', 'USDC', 'USDT', 'DAI', 'BUSD']:
                prices[symbol] = 1.0

        # Get coin IDs for remaining symbols
        coin_ids = []
        symbol_to_coin_id = {}

        for symbol in symbols:
            if symbol not in prices:  # Skip stablecoins
                coin_id = self.symbol_to_id.get(symbol)
                if coin_id:
                    coin_ids.append(coin_id)
                    symbol_to_coin_id[coin_id] = symbol

        if not coin_ids:
            return prices

        # Rate limiting
        self._rate_limit()

        try:
            response = requests.get(
                f"{self.base_url}/simple/price",
                params={
                    'ids': ','.join(coin_ids),
                    'vs_currencies': 'usd'
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                for coin_id, symbol in symbol_to_coin_id.items():
                    price = data.get(coin_id, {}).get('usd')
                    if price:
                        prices[symbol] = price
            else:
                print(f"API error: {response.status_code}")

        except Exception as e:
            print(f"Error fetching prices: {e}")

        return prices

    def get_historical_price(self, symbol: str, date: datetime) -> Optional[float]:
        """Get historical price for a specific date."""
        # Handle stablecoins
        if symbol in ['USD', 'USDC', 'USDT', 'DAI', 'BUSD']:
            return 1.0

        coin_id = self.symbol_to_id.get(symbol)
        if not coin_id:
            return None

        # Format date as DD-MM-YYYY
        date_str = date.strftime("%d-%m-%Y")

        # Rate limiting
        self._rate_limit()

        try:
            response = requests.get(
                f"{self.base_url}/coins/{coin_id}/history",
                params={'date': date_str},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('market_data', {}).get('current_price', {}).get('usd')
            else:
                print(f"API error for {symbol} on {date_str}: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error fetching historical price for {symbol}: {e}")
            return None

    def _rate_limit(self):
        """Implement rate limiting to avoid API throttling."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)

        self.last_request_time = time.time()
