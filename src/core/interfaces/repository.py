# src/core/interfaces/repository.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.entities.transaction import Transaction
from src.core.entities.portfolio import Portfolio, PortfolioSnapshot
from src.core.entities.position import Position


class TransactionRepository(ABC):
    """Abstract repository for transaction persistence."""

    @abstractmethod
    def save(self, transaction: Transaction) -> None:
        """Save a transaction."""
        pass

    @abstractmethod
    def save_batch(self, transactions: List[Transaction]) -> None:
        """Save multiple transactions."""
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        pass

    @abstractmethod
    def get_by_asset(self, asset: str) -> List[Transaction]:
        """Get all transactions for an asset."""
        pass

    @abstractmethod
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Get transactions within date range."""
        pass

    @abstractmethod
    def get_all(self) -> List[Transaction]:
        """Get all transactions."""
        pass

    @abstractmethod
    def delete(self, transaction_id: str) -> None:
        """Delete a transaction."""
        pass


class PortfolioRepository(ABC):
    """Abstract repository for portfolio persistence."""

    @abstractmethod
    def save(self, portfolio: Portfolio) -> None:
        """Save portfolio state."""
        pass

    @abstractmethod
    def load(self, portfolio_id: str) -> Optional[Portfolio]:
        """Load portfolio by ID."""
        pass

    @abstractmethod
    def save_snapshot(self, portfolio_id: str, snapshot: PortfolioSnapshot) -> None:
        """Save a portfolio snapshot."""
        pass

    @abstractmethod
    def get_snapshots(self, portfolio_id: str,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[PortfolioSnapshot]:
        """Get portfolio snapshots within date range."""
        pass

    @abstractmethod
    def delete(self, portfolio_id: str) -> None:
        """Delete a portfolio and all its data."""
        pass


class PriceRepository(ABC):
    """Abstract repository for price data."""

    @abstractmethod
    def save_price(self, asset: str, price: float, timestamp: datetime) -> None:
        """Save a price point."""
        pass

    @abstractmethod
    def get_latest_price(self, asset: str) -> Optional[Dict[str, Any]]:
        """Get latest price for an asset."""
        pass

    @abstractmethod
    def get_historical_price(self, asset: str, date: datetime) -> Optional[float]:
        """Get historical price for a specific date."""
        pass

    @abstractmethod
    def get_price_history(self, asset: str,
                          start_date: datetime,
                          end_date: datetime) -> List[Dict[str, Any]]:
        """Get price history for date range."""
        pass
