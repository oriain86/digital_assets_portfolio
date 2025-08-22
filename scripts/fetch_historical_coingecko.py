# scripts/fetch_historical_coingecko.py

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import time
import requests
from datetime import datetime, date, timedelta
import logging
import pandas as pd

from src.infrastructure.repositories.price_history_repository import PriceHistoryRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoricalPriceFetcherFixed:
    """Fetcher using alternative endpoints."""

    def __init__(self):
        self.price_repo = PriceHistoryRepository()
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'MATIC': 'matic-network',
            'USDT': 'tether',
            'EGLD': 'elrond-erd-2',
            'AXS': 'axie-infinity',
            'FTM': 'fantom',
            'ONE': 'harmony',
            'SAND': 'the-sandbox',
            'HNT': 'helium',
            'NEAR': 'near',
            'LUNA': 'terra-luna-classic',  # Updated
            'USDC': 'usd-coin',
            'AVAX': 'avalanche-2',
            'UST': 'terrausd',  # Added
            'VIRTUAL': 'virtua',  # Fixed
            'SUI': 'sui',
            'FET': 'fetch-ai',
        }

    def fetch_all_assets_current_with_history(self):
        """Fetch using the OHLC endpoint which includes 1-30 days of history."""
        logger.info("Fetching recent price history for all assets...")

        for symbol, coin_id in self.symbol_to_id.items():
            try:
                logger.info(f"Fetching {symbol}...")

                # Get OHLC data (includes last 30 days)
                url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
                params = {
                    'vs_currency': 'usd',
                    'days': '365'  # Can be 1, 7, 14, 30, 90, 180, 365, max
                }

                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    self._process_ohlc_data(symbol, data)
                else:
                    logger.error(f"Failed {symbol}: {response.status_code}")

                time.sleep(10)  # Be very conservative with rate limiting

            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                continue

    def _process_ohlc_data(self, symbol: str, ohlc_data):
        """Process OHLC data format: [[timestamp, open, high, low, close]]"""
        price_records = []

        for candle in ohlc_data:
            timestamp_ms, open_price, high, low, close = candle
            date_str = datetime.fromtimestamp(timestamp_ms / 1000).date().isoformat()

            price_records.append((
                date_str,
                symbol,
                open_price,
                high,
                low,
                close,
                0,  # volume not provided
                0  # market cap not provided
            ))

        if price_records:
            self.price_repo.bulk_insert_prices(price_records)
            logger.info(f"✓ Saved {len(price_records)} days of {symbol} prices")


def main():
    fetcher = HistoricalPriceFetcherFixed()
    fetcher.fetch_all_assets_current_with_history()


if __name__ == "__main__":
    main()
