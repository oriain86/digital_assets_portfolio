# src/core/interfaces/data_source.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path


class DataSource(ABC):
    """Abstract interface for data sources."""

    @abstractmethod
    def load_transactions(self, source: Any) -> List[Dict[str, Any]]:
        """Load transactions from a data source."""
        pass

    @abstractmethod
    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate loaded data."""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        pass


class PriceDataSource(ABC):
    """Abstract interface for price data sources."""

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        pass

    @abstractmethod
    def get_historical_price(self, symbol: str, date: datetime) -> Optional[float]:
        """Get historical price for a symbol on a specific date."""
        pass

    @abstractmethod
    def get_price_history(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get price history for a symbol over a date range."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the data source is available."""
        pass
