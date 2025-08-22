from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from src.core.entities.transaction import Transaction
from src.infrastructure.data_sources.unified_csv_loader import UnifiedCSVLoader
from src.infrastructure.data_sources.excel_loader import ExcelLoader
from src.infrastructure.data_sources.exchange_specific_clients import ExchangeClientFactory

logger = logging.getLogger(__name__)


class UnifiedDataSource:
    """Unified interface for loading transactions from multiple sources."""

    def __init__(self):
        self.csv_loader = UnifiedCSVLoader()
        self.excel_loader = ExcelLoader()

    def load_from_file(self, file_path: str) -> List[Transaction]:
        """Load transactions from file based on extension."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = path.suffix.lower()

        if extension == '.csv':
            return self.csv_loader.load_transactions(file_path)
        elif extension in ['.xlsx', '.xls']:
            return self.excel_loader.load_transactions(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def load_from_exchange(self,
                           exchange: str,
                           start_date: datetime,
                           end_date: datetime,
                           api_key: Optional[str] = None,
                           api_secret: Optional[str] = None) -> List[Transaction]:
        """Load transactions from exchange API."""
        client = ExchangeClientFactory.create_client(
            exchange,
            api_key=api_key,
            api_secret=api_secret
        )

        return client.fetch_transactions(start_date, end_date)

    def merge_transactions(self, *transaction_lists: List[Transaction]) -> List[Transaction]:
        """Merge multiple transaction lists and remove duplicates."""
        all_transactions = []
        seen_ids = set()

        for tx_list in transaction_lists:
            for tx in tx_list:
                if tx.transaction_id not in seen_ids:
                    all_transactions.append(tx)
                    seen_ids.add(tx.transaction_id)

        # Sort by timestamp
        all_transactions.sort(key=lambda x: x.timestamp)

        return all_transactions
