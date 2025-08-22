# src/application/use_cases/load_transactions.py

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from src.core.entities.transaction import Transaction
from src.infrastructure.data_sources.unified_csv_loader import UnifiedCSVLoader
from src.application.services.transaction_processor import TransactionProcessor

logger = logging.getLogger(__name__)


class LoadTransactionsUseCase:
    """
    Use case for loading transactions from various sources.
    Coordinates between data sources and transaction processing.
    """

    def __init__(self):
        self.csv_loader = UnifiedCSVLoader()
        self.processor = TransactionProcessor()
        self.supported_formats = {'.csv', '.xlsx', '.json'}

    def execute(self, file_path: str) -> Dict[str, Any]:
        """
        Load and process transactions from a file.

        Args:
            file_path: Path to the transaction file

        Returns:
            Dictionary with results including transactions and any errors
        """
        logger.info(f"Loading transactions from {file_path}")

        # Validate file
        path = Path(file_path)
        if not path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}',
                'transactions': []
            }

        # Determine file type and load accordingly
        file_extension = path.suffix.lower()

        if file_extension not in self.supported_formats:
            return {
                'success': False,
                'error': f'Unsupported file format: {file_extension}',
                'transactions': []
            }

        try:
            if file_extension == '.csv':
                transactions = self._load_from_csv(file_path)
            elif file_extension == '.xlsx':
                transactions = self._load_from_excel(file_path)
            elif file_extension == '.json':
                transactions = self._load_from_json(file_path)
            else:
                raise ValueError(f"Unsupported format: {file_extension}")

            # Process and validate transactions
            processed_transactions = self._process_transactions(transactions)

            # Generate summary
            summary = self._generate_summary(processed_transactions)

            return {
                'success': True,
                'transactions': processed_transactions,
                'summary': summary,
                'errors': self.csv_loader.errors,
                'warnings': self.csv_loader.warnings
            }

        except Exception as e:
            logger.error(f"Failed to load transactions: {e}")
            return {
                'success': False,
                'error': str(e),
                'transactions': []
            }

    def _load_from_csv(self, file_path: str) -> List[Transaction]:
        """Load transactions from CSV file."""
        return self.csv_loader.load_transactions(file_path)

    def _load_from_excel(self, file_path: str) -> List[Transaction]:
        """Load transactions from Excel file."""
        # For now, we'll use pandas to read Excel and convert to CSV format
        try:
            import pandas as pd
            df = pd.read_excel(file_path)

            # Save as temporary CSV and load
            temp_csv = Path(file_path).with_suffix('.csv')
            df.to_csv(temp_csv, index=False)

            transactions = self.csv_loader.load_transactions(str(temp_csv))

            # Clean up temp file
            temp_csv.unlink()

            return transactions
        except ImportError:
            raise ImportError("openpyxl required for Excel support. Install with: pip install openpyxl")

    def _load_from_json(self, file_path: str) -> List[Transaction]:
        """Load transactions from JSON file."""
        import json

        with open(file_path, 'r') as f:
            data = json.load(f)

        transactions = []
        for tx_data in data.get('transactions', []):
            try:
                tx = Transaction.from_dict(tx_data)
                transactions.append(tx)
            except Exception as e:
                logger.error(f"Failed to parse transaction: {e}")

        return transactions

    def _process_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """Process and enhance transactions."""
        # Sort chronologically
        transactions.sort(key=lambda x: x.timestamp)

        # Match conversions - use the correct method name
        transactions = self.processor._match_conversions(transactions)

        # Validate transaction order - use the correct method name
        transactions = self.processor._validate_transaction_order(transactions)

        return transactions

    def _generate_summary(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Generate summary statistics for loaded transactions."""
        if not transactions:
            return {}

        summary = {
            'total_count': len(transactions),
            'date_range': {
                'start': min(tx.timestamp for tx in transactions).isoformat(),
                'end': max(tx.timestamp for tx in transactions).isoformat()
            },
            'by_type': {},
            'by_asset': {},
            'by_exchange': {}
        }

        # Count by type
        for tx in transactions:
            tx_type = tx.type.value
            summary['by_type'][tx_type] = summary['by_type'].get(tx_type, 0) + 1

            # Count by asset
            summary['by_asset'][tx.asset] = summary['by_asset'].get(tx.asset, 0) + 1

            # Count by exchange
            if tx.exchange:
                summary['by_exchange'][tx.exchange] = summary['by_exchange'].get(tx.exchange, 0) + 1

        return summary
