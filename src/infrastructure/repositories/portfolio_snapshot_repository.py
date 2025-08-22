# src/infrastructure/repositories/portfolio_snapshot_repository.py
import sqlite3
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional


class PortfolioSnapshotRepository:
    """Repository for storing pre-calculated portfolio snapshots."""

    def __init__(self, db_path: str = "data/portfolio_snapshots.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize snapshot database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_snapshots (
                    date TEXT PRIMARY KEY,
                    total_value REAL NOT NULL,
                    cash_balance REAL NOT NULL,
                    positions TEXT NOT NULL,  -- JSON
                    fund_cycle INTEGER,
                    daily_return REAL,
                    cumulative_return REAL,
                    drawdown REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_date 
                ON daily_snapshots(date DESC)
            """)

            # Fund cycle tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fund_cycles (
                    cycle_id INTEGER PRIMARY KEY,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    initial_deposit REAL NOT NULL,
                    final_value REAL,
                    total_return REAL,
                    status TEXT DEFAULT 'active'
                )
            """)

    def save_snapshots(self, snapshots: List[Dict]):
        """Bulk save daily snapshots."""
        with sqlite3.connect(self.db_path) as conn:
            for snapshot in snapshots:
                conn.execute("""
                    INSERT OR REPLACE INTO daily_snapshots
                    (date, total_value, cash_balance, positions, fund_cycle, 
                     daily_return, cumulative_return, drawdown)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot['date'].isoformat(),
                    snapshot['total_value'],
                    snapshot['cash_balance'],
                    json.dumps(snapshot['positions']),
                    snapshot.get('fund_cycle'),
                    snapshot.get('daily_return'),
                    snapshot.get('cumulative_return'),
                    snapshot.get('drawdown')
                ))

    def get_all_snapshots(self) -> List[Dict]:
        """Get all snapshots for dashboard."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM daily_snapshots 
                ORDER BY date
            """)

            snapshots = []
            for row in cursor:
                snapshots.append({
                    'date': datetime.fromisoformat(row['date']).date(),
                    'total_value': row['total_value'],
                    'cash_balance': row['cash_balance'],
                    'positions': json.loads(row['positions']),
                    'fund_cycle': row['fund_cycle'],
                    'daily_return': row['daily_return'],
                    'cumulative_return': row['cumulative_return'],
                    'drawdown': row['drawdown']
                })

            return snapshots
