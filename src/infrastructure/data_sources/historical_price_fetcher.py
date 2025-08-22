# src/infrastructure/data_sources/historical_price_fetcher.py

import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import logging
import requests

from src.infrastructure.repositories.price_history_repository import PriceHistoryRepository

logger = logging.getLogger(__name__)


class HistoricalPriceFetcher:
    """Fetches and stores historical price data."""

    def __init__(self, price_repo: PriceHistoryRepository = None):
        self.price_repo = price_repo or PriceHistoryRepository()
        self.base_url = "https://api.coingecko.com/api/v3"
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2',
            'NEAR': 'near',
            'FTM': 'fantom',
            'ONE': 'harmony',
            'SAND': 'the-sandbox',
            'HNT': 'helium',
            'AXS': 'axie-infinity',
            'EGLD': 'elrond-erd-2',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'FET': 'fetch-ai',
            'VIRTUAL': 'virtual-protocol',
            'SUI': 'sui',
            # Add more mappings as needed
        }

    def fetch_all_historical_prices(self, start_date: date, end_date: date = None):
        """Fetch historical prices for all assets in the portfolio."""
        if end_date is None:
            end_date = date.today()

        # Get unique assets from your transactions
        assets = self._get_portfolio_assets()

        total_assets = len(assets)
        logger.info(f"Fetching historical prices for {total_assets} assets from {start_date} to {end_date}")

        for i, asset in enumerate(assets):
            if asset == 'USD':
                continue  # Skip USD

            logger.info(f"Fetching {asset} ({i + 1}/{total_assets})...")

            try:
                self.fetch_historical_prices(asset, start_date, end_date)
                time.sleep(1.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to fetch {asset}: {e}")
                continue

    def fetch_historical_prices(self, asset: str, start_date: date, end_date: date):
        """Fetch historical prices for a single asset."""
        # Check if we already have this data
        if not self.price_repo.needs_fetch(asset, start_date, end_date):
            logger.info(f"Already have {asset} data for {start_date} to {end_date}")
            return

        coin_id = self.symbol_to_id.get(asset.upper())
        if not coin_id:
            logger.warning(f"No CoinGecko ID mapping for {asset}")
            return

        # CoinGecko wants Unix timestamps
        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp())

        url = f"{self.base_url}/coins/{coin_id}/market_chart/range"
        params = {
            'vs_currency': 'usd',
            'from': start_ts,
            'to': end_ts
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Process the response
            prices = []
            if 'prices' in data:
                for timestamp, price in data['prices']:
                    price_date = datetime.fromtimestamp(timestamp / 1000).date()
                    prices.append({
                        'date': price_date.isoformat(),
                        'close': price
                    })

            # Save to database
            if prices:
                self.price_repo.save_daily_prices(asset, prices)
                logger.info(f"Saved {len(prices)} price points for {asset}")

        except Exception as e:
            logger.error(f"Error fetching {asset} prices: {e}")
            raise

    def _get_portfolio_assets(self) -> List[str]:
        """Get list of all assets traded in the portfolio."""
        # This should read from your transactions
        # For now, returning a static list based on your portfolio
        return [
            'BTC', 'ETH', 'BNB', 'SOL', 'MATIC', 'AVAX',
            'NEAR', 'FTM', 'ONE', 'SAND', 'HNT', 'AXS',
            'EGLD', 'USDT', 'USDC', 'FET', 'VIRTUAL', 'SUI'
        ]
