# src/infrastructure/repositories/price_history_repository.py

import sqlite3
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PriceHistoryRepository:
    """Repository for storing and retrieving historical price data."""

    def __init__(self, db_path: str = "data/price_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize price history database with optimized schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable optimizations
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")

            # Main price table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_prices (
                    date TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL NOT NULL,
                    volume REAL,
                    market_cap REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (date, asset)
                )
            """)

            # Optimized compound index
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_asset_date 
                ON daily_prices(asset, date)
            """)

            # Track what we've fetched
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fetch_status (
                    asset TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (asset, start_date, end_date)
                )
            """)

    def bulk_insert_prices(self, prices: List[Tuple[str, str, float, float, float, float, float, float]]):
        """Bulk insert price data for efficiency."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO daily_prices 
                (date, asset, open, high, low, close, volume, market_cap)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, prices)
            logger.info(f"Inserted {len(prices)} price records")

    def get_price(self, asset: str, target_date: date) -> Optional[Decimal]:
        """Get closing price for an asset on a specific date."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT close FROM daily_prices 
                WHERE asset = ? AND date = ?
            """, (asset.upper(), target_date.isoformat())).fetchone()

            return Decimal(str(result[0])) if result else None

    def get_price_range(self, asset: str, start_date: date, end_date: date) -> Dict[date, Decimal]:
        """Get all closing prices for an asset in a date range."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT date, close FROM daily_prices 
                WHERE asset = ? AND date >= ? AND date <= ?
                ORDER BY date
            """, (asset.upper(), start_date.isoformat(), end_date.isoformat()))

            return {
                datetime.fromisoformat(row['date']).date(): Decimal(str(row['close']))
                for row in cursor
            }

    def get_all_prices_on_date(self, target_date: date) -> Dict[str, Decimal]:
        """Get all asset prices for a specific date."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT asset, close 
                FROM daily_prices 
                WHERE date = ?
            """, (target_date.isoformat(),))

            return {
                row['asset']: Decimal(str(row['close']))
                for row in cursor
            }

    def is_data_complete(self, asset: str, start_date: date, end_date: date) -> bool:
        """Check if we have complete data for date range."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT COUNT(DISTINCT date) 
                FROM daily_prices 
                WHERE asset = ? AND date >= ? AND date <= ?
            """, (asset.upper(), start_date.isoformat(), end_date.isoformat())).fetchone()

            actual_days = result[0] if result else 0
            expected_days = (end_date - start_date).days + 1

            # 90% threshold for weekends/holidays
            return actual_days >= (expected_days * 0.9)

    def save_daily_prices(self, asset: str, prices: List[Dict]):
        """Save daily prices for an asset (compatibility method)."""
        # Convert to bulk insert format
        price_records = []
        for price_data in prices:
            price_records.append((
                price_data['date'],
                asset.upper(),
                price_data.get('open', price_data['close']),
                price_data.get('high', price_data['close']),
                price_data.get('low', price_data['close']),
                price_data['close'],
                price_data.get('volume', 0),
                price_data.get('market_cap', 0)
            ))

        if price_records:
            self.bulk_insert_prices(price_records)

    def needs_fetch(self, asset: str, start_date: date, end_date: date) -> bool:
        """Check if we need to fetch data for this range."""
        return not self.is_data_complete(asset, start_date, end_date)
