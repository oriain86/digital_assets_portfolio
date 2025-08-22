# src/application/services/transaction_processor.py

import pandas as pd
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import re
from collections import defaultdict

from src.core.entities.transaction import Transaction, TransactionType
from src.core.entities.portfolio import Portfolio
from src.shared.utils.exceptions import ValidationError


class TransactionProcessor:
    """
    Service responsible for processing raw transaction data.

    This service handles:
    - Parsing and cleaning transaction data from various sources
    - Matching related transactions (e.g., conversions)
    - Handling exchange-specific formats
    - Validating transaction integrity
    """

    def __init__(self):
        self.conversion_pairs = []
        self.unmatched_conversions = []
        self.errors = []
        self.transfer_pairs = {}

    def parse_csv_transactions(self, file_path: str) -> List[Transaction]:
        """Parse transactions from CSV file."""
        try:
            # Read CSV with proper parsing
            df = pd.read_csv(file_path)

            # Clean column names
            df.columns = df.columns.str.strip()

            transactions = []

            for idx, row in df.iterrows():
                try:
                    transaction = self._parse_transaction_row(row, idx)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    self.errors.append(f"Row {idx + 2}: {str(e)}")
                    continue

            # Post-process transactions
            transactions = self._match_conversions(transactions)
            transfer_pairs = self.match_transfer_pairs(transactions)
            transactions = self._validate_transaction_order(transactions)

            # Store transfer pairs for later use
            self.transfer_pairs = transfer_pairs

            return transactions

        except Exception as e:
            raise ValidationError(f"Failed to parse CSV file: {str(e)}")

    def _parse_transaction_row(self, row: pd.Series, row_index: int) -> Optional[Transaction]:
        """Parse a single transaction row."""
        # Parse timestamp
        timestamp = self._parse_timestamp(row['timestamp'])

        # Parse transaction type
        try:
            tx_type = TransactionType.from_string(row['type'])
        except ValueError:
            # Handle special cases
            type_str = str(row['type']).strip()
            if 'stake' in type_str.lower():
                tx_type = TransactionType.STAKING
            elif 'unstake' in type_str.lower():
                tx_type = TransactionType.UNSTAKING
            else:
                raise ValueError(f"Unknown transaction type: {type_str}")

        # Parse amounts and prices
        amount = self._parse_decimal(row['amount'])
        price_usd = self._parse_currency_value(row.get('price_usd'))
        total_usd = self._parse_currency_value(row.get('total_usd'))
        fee_usd = self._parse_currency_value(row.get('fee_usd'))

        # Clean asset symbol
        asset = str(row['asset']).strip().upper()

        # Handle special assets
        if asset in ['WETH', 'WBTC']:
            # Wrapped tokens - treat as underlying
            asset = asset[1:]  # Remove 'W' prefix

        return Transaction(
            timestamp=timestamp,
            type=tx_type,
            asset=asset,
            amount=amount,
            price_usd=price_usd,
            total_usd=total_usd,
            fee_usd=fee_usd,
            exchange=str(row.get('exchange', '')).strip() if pd.notna(row.get('exchange')) else None,
            transaction_id=str(row.get('transaction_id', '')).strip() if pd.notna(row.get('transaction_id')) else None,
            notes=str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else None
        )

    def _parse_timestamp(self, value) -> datetime:
        """Parse various timestamp formats."""
        if pd.isna(value):
            raise ValueError("Missing timestamp")

        timestamp_str = str(value).strip()

        # Try different date formats
        formats = [
            "%d.%m.%Y %H:%M:%S",  # European format with time
            "%Y-%m-%d %H:%M:%S",  # ISO format with time
            "%m/%d/%Y %H:%M:%S",  # US format with time
            "%d.%m.%Y",  # European format without time
            "%Y-%m-%d",  # ISO format without time
            "%m/%d/%Y",  # US format without time
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse timestamp: {timestamp_str}")

    def _parse_decimal(self, value) -> Decimal:
        """Parse decimal value handling various formats."""
        if pd.isna(value):
            raise ValueError("Missing numeric value")

        # Convert to string and clean
        value_str = str(value).strip()

        # Remove any thousand separators
        value_str = value_str.replace(',', '')

        try:
            return Decimal(value_str)
        except:
            raise ValueError(f"Unable to parse decimal: {value_str}")

    def _parse_currency_value(self, value) -> Optional[Decimal]:
        """Parse currency values that may include $ symbol."""
        if pd.isna(value) or value == '' or value is None:
            return None

        value_str = str(value).strip()

        # Remove currency symbols and whitespace
        value_str = re.sub(r'[$,\s]', '', value_str)

        # Handle parentheses for negative values
        if value_str.startswith('(') and value_str.endswith(')'):
            value_str = '-' + value_str[1:-1]

        if value_str == '' or value_str == '-':
            return None

        try:
            return Decimal(value_str)
        except:
            raise ValueError(f"Unable to parse currency value: {value_str}")

    def _match_conversions(self, transactions: List[Transaction]) -> List[Transaction]:
        """Match conversion pairs and link them."""
        # Group transactions by timestamp and exchange
        grouped = defaultdict(list)

        for tx in transactions:
            if tx.type in [TransactionType.CONVERT_FROM, TransactionType.CONVERT_TO]:
                key = (tx.timestamp, tx.exchange)
                grouped[key].append(tx)

        # Match pairs
        for (timestamp, exchange), group in grouped.items():
            from_txs = [tx for tx in group if tx.type == TransactionType.CONVERT_FROM]
            to_txs = [tx for tx in group if tx.type == TransactionType.CONVERT_TO]

            # Try to match by value if single pair
            if len(from_txs) == 1 and len(to_txs) == 1:
                from_tx = from_txs[0]
                to_tx = to_txs[0]

                # Link the transactions
                conversion_id = f"conv_{from_tx.transaction_id[:8]}"
                from_tx.matched_transaction_id = conversion_id
                to_tx.matched_transaction_id = conversion_id

                self.conversion_pairs.append((from_tx, to_tx))
            else:
                # Multiple conversions at same time - need more complex matching
                self.unmatched_conversions.extend(group)

        return transactions

    def match_transfer_pairs(self, transactions: List[Transaction]) -> Dict[str, str]:
        """
        Match transfer out/in pairs to identify self-custody transfers.
        Returns mapping of transfer_out_id -> transfer_in_id
        """
        transfer_pairs = {}

        # Group transactions by asset and sort by time
        by_asset = defaultdict(list)
        for tx in transactions:
            if tx.asset not in by_asset:
                by_asset[tx.asset] = []
            by_asset[tx.asset].append(tx)

        for asset, asset_txs in by_asset.items():
            asset_txs.sort(key=lambda x: x.timestamp)

            # Look for transfer out followed by transfer in
            for i, tx in enumerate(asset_txs):
                if tx.type.value in ['Send', 'Transfer Out']:
                    # Look for matching transfer in within 7 days
                    for j in range(i + 1, min(i + 20, len(asset_txs))):
                        next_tx = asset_txs[j]
                        time_diff = (next_tx.timestamp - tx.timestamp).days

                        if time_diff > 7:
                            break

                        if (next_tx.type.value in ['Receive', 'Transfer In'] and
                                abs(next_tx.amount - tx.amount) < tx.amount * Decimal('0.01')):  # Within 1% (fees)

                            transfer_pairs[tx.transaction_id] = next_tx.transaction_id
                            print(f"Matched transfer pair for {asset}: {tx.amount}")
                            break

        return transfer_pairs

    def _validate_transaction_order(self, transactions: List[Transaction]) -> List[Transaction]:
        """Validate and sort transactions chronologically."""
        # Sort by timestamp
        transactions.sort(key=lambda x: x.timestamp)

        # Validate running balances
        balances = defaultdict(Decimal)

        for tx in transactions:
            if tx.type.is_acquisition():
                balances[tx.asset] += tx.amount
            elif tx.type.is_disposal():
                balances[tx.asset] -= tx.amount

                # Check for negative balance
                if balances[tx.asset] < 0:
                    self.errors.append(
                        f"Negative balance for {tx.asset} at {tx.timestamp}: "
                        f"balance={balances[tx.asset]}, transaction={tx.amount}"
                    )

        return transactions

    def process_transactions_to_portfolio(self, transactions: List[Transaction],
                                          portfolio: Portfolio) -> Dict[str, any]:
        """Process all transactions through a portfolio."""
        results = {
            'processed': 0,
            'errors': [],
            'realized_gains': [],
            'conversion_pairs': self.conversion_pairs,
            'transfer_pairs': self.transfer_pairs
        }

        for tx in transactions:
            try:
                realized_pnl = portfolio.process_transaction(tx)

                if realized_pnl is not None:
                    results['realized_gains'].append({
                        'timestamp': tx.timestamp,
                        'asset': tx.asset,
                        'amount': tx.amount,
                        'realized_pnl': realized_pnl,
                        'transaction_id': tx.transaction_id
                    })

                results['processed'] += 1

            except Exception as e:
                results['errors'].append({
                    'transaction': tx.to_dict(),
                    'error': str(e)
                })

        return results

    def reconcile_transactions(self, transactions: List[Transaction]) -> Dict[str, any]:
        """Perform reconciliation checks on transactions."""
        reconciliation = {
            'total_transactions': len(transactions),
            'by_type': defaultdict(int),
            'by_asset': defaultdict(int),
            'by_exchange': defaultdict(int),
            'date_range': None,
            'missing_prices': [],
            'high_fees': [],
            'duplicate_suspects': []
        }

        # Count by type, asset, exchange
        for tx in transactions:
            reconciliation['by_type'][tx.type.value] += 1
            reconciliation['by_asset'][tx.asset] += 1
            if tx.exchange:
                reconciliation['by_exchange'][tx.exchange] += 1

        # Date range
        if transactions:
            reconciliation['date_range'] = {
                'start': min(tx.timestamp for tx in transactions),
                'end': max(tx.timestamp for tx in transactions)
            }

        # Check for missing prices on trades
        for tx in transactions:
            if tx.type in [TransactionType.BUY, TransactionType.SELL]:
                if not tx.price_usd and not tx.total_usd:
                    reconciliation['missing_prices'].append({
                        'timestamp': tx.timestamp,
                        'type': tx.type.value,
                        'asset': tx.asset,
                        'amount': float(tx.amount)
                    })

        # Check for high fees (> 2% of transaction value)
        for tx in transactions:
            if tx.fee_usd and tx.total_usd:
                fee_percent = (tx.fee_usd / tx.total_usd) * 100
                if fee_percent > 2:
                    reconciliation['high_fees'].append({
                        'timestamp': tx.timestamp,
                        'type': tx.type.value,
                        'asset': tx.asset,
                        'fee_percent': float(fee_percent)
                    })

        # Check for potential duplicates
        seen = set()
        for tx in transactions:
            # Create a signature for comparison
            sig = (tx.timestamp, tx.type, tx.asset, tx.amount)
            if sig in seen:
                reconciliation['duplicate_suspects'].append({
                    'timestamp': tx.timestamp,
                    'type': tx.type.value,
                    'asset': tx.asset,
                    'amount': float(tx.amount)
                })
            seen.add(sig)

        return dict(reconciliation)

