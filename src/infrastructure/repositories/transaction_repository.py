# src/infrastructure/repositories/transaction_repository.py

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Protocol
from datetime import datetime
from decimal import Decimal
import logging
from contextlib import contextmanager

from src.core.entities.transaction import Transaction, TransactionType
from src.shared.utils.exceptions import DataSourceError

logger = logging.getLogger(__name__)


class TransactionRepositoryProtocol(Protocol):
    """Protocol for transaction repository implementations."""

    def save(self, transaction: Transaction) -> None: ...

    def save_batch(self, transactions: List[Transaction]) -> None: ...

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]: ...

    def get_by_asset(self, asset: str) -> List[Transaction]: ...

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Transaction]: ...

    def get_all(self) -> List[Transaction]: ...

    def delete(self, transaction_id: str) -> None: ...


class SQLiteTransactionRepository:
    """SQLite implementation of transaction repository."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "data/transactions.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Create schema version table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Check current version
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_version")
            current_version = cursor.fetchone()[0] or 0

            # Apply migrations
            if current_version < self.SCHEMA_VERSION:
                self._apply_migrations(conn, current_version)

    def _apply_migrations(self, conn: sqlite3.Connection, current_version: int):
        """Apply database migrations."""
        if current_version < 1:
            # Initial schema
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    price_usd TEXT,
                    total_usd TEXT,
                    fee_usd TEXT,
                    exchange TEXT,
                    notes TEXT,
                    cost_basis TEXT,
                    realized_gain_loss TEXT,
                    matched_transaction_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_asset ON transactions(asset)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON transactions(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON transactions(type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exchange ON transactions(exchange)")

            # Update schema version
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (1,))

    def save(self, transaction: Transaction) -> None:
        """Save a transaction."""
        with self._get_connection() as conn:
            self._save_transaction(conn, transaction)

    def save_batch(self, transactions: List[Transaction]) -> None:
        """Save multiple transactions efficiently."""
        with self._get_connection() as conn:
            for transaction in transactions:
                self._save_transaction(conn, transaction)
            logger.info(f"Saved {len(transactions)} transactions")

    def _save_transaction(self, conn: sqlite3.Connection, transaction: Transaction):
        """Save a single transaction to the database."""
        conn.execute("""
            INSERT OR REPLACE INTO transactions (
                transaction_id, timestamp, type, asset, amount,
                price_usd, total_usd, fee_usd, exchange, notes,
                cost_basis, realized_gain_loss, matched_transaction_id,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            transaction.transaction_id,
            transaction.timestamp.isoformat(),
            transaction.type.value,
            transaction.asset,
            str(transaction.amount),
            str(transaction.price_usd) if transaction.price_usd else None,
            str(transaction.total_usd) if transaction.total_usd else None,
            str(transaction.fee_usd) if transaction.fee_usd else None,
            transaction.exchange,
            transaction.notes,
            str(getattr(transaction, 'cost_basis', None)) if hasattr(transaction, 'cost_basis') else None,
            str(getattr(transaction, 'realized_gain_loss', None)) if hasattr(transaction,
                                                                             'realized_gain_loss') else None,
            getattr(transaction, 'matched_transaction_id', None)
        ))

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transactions WHERE transaction_id = ?",
                (transaction_id,)
            )
            row = cursor.fetchone()
            return self._row_to_transaction(row) if row else None

    def get_by_asset(self, asset: str) -> List[Transaction]:
        """Get all transactions for an asset."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transactions WHERE asset = ? ORDER BY timestamp",
                (asset,)
            )
            return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Get transactions within date range."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM transactions 
                   WHERE timestamp >= ? AND timestamp <= ?
                   ORDER BY timestamp""",
                (start_date.isoformat(), end_date.isoformat())
            )
            return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def get_all(self) -> List[Transaction]:
        """Get all transactions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY timestamp")
            return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def delete(self, transaction_id: str) -> None:
        """Delete a transaction."""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM transactions WHERE transaction_id = ?",
                (transaction_id,)
            )
            logger.info(f"Deleted transaction {transaction_id}")

    def _row_to_transaction(self, row: sqlite3.Row) -> Transaction:
        """Convert database row to Transaction entity."""
        try:
            tx = Transaction(
                timestamp=datetime.fromisoformat(row['timestamp']),
                type=TransactionType.from_string(row['type']),
                asset=row['asset'],
                amount=Decimal(row['amount']),
                price_usd=Decimal(row['price_usd']) if row['price_usd'] else None,
                total_usd=Decimal(row['total_usd']) if row['total_usd'] else None,
                fee_usd=Decimal(row['fee_usd']) if row['fee_usd'] else None,
                exchange=row['exchange'],
                transaction_id=row['transaction_id'],
                notes=row['notes']
            )

            # Set additional fields - Fixed to handle None values properly
            if row['cost_basis'] and row['cost_basis'] != 'None':
                try:
                    tx.cost_basis = Decimal(row['cost_basis'])
                except:
                    pass  # Ignore if conversion fails

            if row['realized_gain_loss'] and row['realized_gain_loss'] != 'None':
                try:
                    tx.realized_gain_loss = Decimal(row['realized_gain_loss'])
                except:
                    pass  # Ignore if conversion fails

            if row['matched_transaction_id'] and row['matched_transaction_id'] != 'None':
                tx.matched_transaction_id = row['matched_transaction_id']

            return tx
        except Exception as e:
            logger.error(f"Failed to convert row to transaction: {e}")
            raise DataSourceError(f"Failed to create Transaction from row: {e}")
