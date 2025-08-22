# src/infrastructure/data_sources/unified_csv_loader.py

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.core.entities.transaction import Transaction, TransactionType
from src.shared.validators import (
    validate_datetime, validate_positive_decimal,
    validate_asset_symbol, validate_exchange_name
)
from src.shared.utils.exceptions import ValidationError, DataSourceError

logger = logging.getLogger(__name__)


class UnifiedCSVLoader:
    """
    Loads and processes the unified CSV transaction file.
    Handles data cleaning, validation, and conversion to domain entities.
    """

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.processed_count = 0

    def load_transactions(self, file_path: str) -> List[Transaction]:
        """Load transactions from unified CSV file."""
        try:
            # Read CSV file
            df = self._read_csv(file_path)

            # Validate structure
            self._validate_csv_structure(df)

            # Clean data
            df = self._clean_data(df)

            # Process transactions
            transactions = self._process_transactions(df)

            # Post-process (sort, validate integrity)
            transactions = self._post_process_transactions(transactions)

            logger.info(f"Loaded {len(transactions)} transactions from {file_path}")
            return transactions

        except Exception as e:
            raise DataSourceError(f"Failed to load CSV file: {str(e)}")

    def _read_csv(self, file_path: str) -> pd.DataFrame:
        """Read CSV file with proper encoding handling."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']

        for encoding in encodings:
            try:
                df = pd.read_csv(path, encoding=encoding)
                logger.info(f"Successfully read CSV with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                continue

        raise DataSourceError("Failed to read CSV file with any supported encoding")

    def _validate_csv_structure(self, df: pd.DataFrame):
        """Validate CSV has required columns."""
        required_columns = [
            'timestamp', 'type', 'asset', 'amount'
        ]

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")

        # Check for essential optional columns
        optional_columns = ['price_usd', 'total_usd', 'fee_usd', 'exchange', 'transaction_id', 'notes']
        for col in optional_columns:
            if col not in df.columns:
                self.warnings.append(f"Optional column '{col}' not found")

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize data."""
        # Make a copy to avoid modifying original
        df = df.copy()

        # Strip whitespace from string columns
        string_columns = ['type', 'asset', 'exchange', 'transaction_id', 'notes']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # Replace 'nan' strings with actual NaN
                df[col] = df[col].replace(['nan', 'None', ''], pd.NA)

        # Clean numeric columns
        numeric_columns = ['amount', 'price_usd', 'total_usd', 'fee_usd']
        for col in numeric_columns:
            if col in df.columns:
                # Remove currency symbols and commas
                df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                # Convert to numeric
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Drop rows with invalid required fields
        required_valid = df[['timestamp', 'type', 'asset', 'amount']].notna().all(axis=1)
        invalid_count = (~required_valid).sum()

        if invalid_count > 0:
            self.warnings.append(f"Dropped {invalid_count} rows with missing required fields")
            df = df[required_valid]

        return df

    def _process_transactions(self, df: pd.DataFrame) -> List[Transaction]:
        """Process DataFrame rows into Transaction entities."""
        transactions = []

        for idx, row in df.iterrows():
            try:
                transaction = self._create_transaction(row, idx)
                if transaction:
                    transactions.append(transaction)
                    self.processed_count += 1
            except Exception as e:
                self.errors.append({
                    'row': idx + 2,  # +2 for header and 0-indexing
                    'error': str(e),
                    'data': row.to_dict()
                })

        return transactions

    def _create_transaction(self, row: pd.Series, row_index: int) -> Optional[Transaction]:
        """Create Transaction entity from DataFrame row."""
        try:
            # Parse timestamp
            timestamp = validate_datetime(row['timestamp'], "timestamp")

            # Parse transaction type
            tx_type = self._parse_transaction_type(row['type'])

            # Parse asset
            asset = validate_asset_symbol(row['asset'])

            # Parse amount
            amount = validate_positive_decimal(row['amount'], "amount")

            # Parse optional fields
            price_usd = None
            if pd.notna(row.get('price_usd')):
                price_usd = validate_positive_decimal(row['price_usd'], "price_usd")

            total_usd = None
            if pd.notna(row.get('total_usd')):
                total_usd = validate_positive_decimal(row['total_usd'], "total_usd")

            fee_usd = None
            if pd.notna(row.get('fee_usd')):
                fee_usd = validate_positive_decimal(row['fee_usd'], "fee_usd")

            exchange = None
            if pd.notna(row.get('exchange')):
                exchange = validate_exchange_name(row['exchange'])

            transaction_id = None
            if pd.notna(row.get('transaction_id')):
                transaction_id = str(row['transaction_id']).strip()

            notes = None
            if pd.notna(row.get('notes')):
                notes = str(row['notes']).strip()

            # Create transaction
            return Transaction(
                timestamp=timestamp,
                type=tx_type,
                asset=asset,
                amount=amount,
                price_usd=price_usd,
                total_usd=total_usd,
                fee_usd=fee_usd,
                exchange=exchange,
                transaction_id=transaction_id,
                notes=notes
            )

        except Exception as e:
            raise ValidationError(f"Row {row_index + 2}: {str(e)}")

    def _parse_transaction_type(self, type_str: str) -> TransactionType:
        """Parse transaction type string to enum."""
        try:
            return TransactionType.from_string(type_str)
        except ValueError:
            # Handle special cases or variations
            type_lower = type_str.lower()

            if 'stake' in type_lower and 'un' not in type_lower:
                return TransactionType.STAKING
            elif 'unstake' in type_lower:
                return TransactionType.UNSTAKING
            elif 'interest' in type_lower:
                return TransactionType.INTEREST
            elif 'airdrop' in type_lower:
                return TransactionType.AIRDROP
            elif 'convert' in type_lower and 'from' in type_lower:
                return TransactionType.CONVERT_FROM
            elif 'convert' in type_lower and 'to' in type_lower:
                return TransactionType.CONVERT_TO
            else:
                raise ValueError(f"Unknown transaction type: {type_str}")

    def _post_process_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """Post-process transactions (sort, validate, etc.)."""
        # Sort by timestamp
        transactions.sort(key=lambda x: x.timestamp)

        # Validate chronological integrity
        self._validate_chronological_integrity(transactions)

        # Match conversion pairs
        self._match_conversion_pairs(transactions)

        return transactions

    def _validate_chronological_integrity(self, transactions: List[Transaction]):
        """Validate transactions are in chronological order and check balances."""
        balances = {}

        for i, tx in enumerate(transactions):
            asset = tx.asset

            if tx.type.is_acquisition():
                balances[asset] = balances.get(asset, 0) + float(tx.amount)
            elif tx.type.is_disposal():
                balances[asset] = balances.get(asset, 0) - float(tx.amount)

                if balances[asset] < -0.00000001:  # Small tolerance for rounding
                    self.warnings.append(
                        f"Negative balance detected for {asset} at {tx.timestamp}: "
                        f"balance={balances[asset]:.8f}, transaction amount={float(tx.amount)}"
                    )

    def _match_conversion_pairs(self, transactions: List[Transaction]):
        """Match conversion from/to pairs."""
        # Group conversions by timestamp and exchange
        conversions = {}

        for tx in transactions:
            if tx.type in [TransactionType.CONVERT_FROM, TransactionType.CONVERT_TO]:
                key = (tx.timestamp, tx.exchange)
                if key not in conversions:
                    conversions[key] = {'from': [], 'to': []}

                if tx.type == TransactionType.CONVERT_FROM:
                    conversions[key]['from'].append(tx)
                else:
                    conversions[key]['to'].append(tx)

        # Match pairs
        for key, group in conversions.items():
            from_txs = group['from']
            to_txs = group['to']

            if len(from_txs) == 1 and len(to_txs) == 1:
                # Simple case: one-to-one conversion
                from_tx = from_txs[0]
                to_tx = to_txs[0]

                # Create matching ID
                match_id = f"conv_{from_tx.transaction_id[:8] if from_tx.transaction_id else 'unknown'}"
                from_tx.matched_transaction_id = match_id
                to_tx.matched_transaction_id = match_id
            else:
                # Complex case: multiple conversions at same time
                self.warnings.append(
                    f"Unmatched conversion at {key[0]}: "
                    f"{len(from_txs)} from, {len(to_txs)} to"
                )

    def get_summary(self) -> Dict[str, Any]:
        """Get loading summary with statistics and issues."""
        return {
            'processed_count': self.processed_count,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors[:10],  # First 10 errors
            'warnings': self.warnings[:10],  # First 10 warnings
            'success': len(self.errors) == 0
        }
