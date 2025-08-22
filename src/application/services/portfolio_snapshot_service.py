# src/application/services/portfolio_snapshot_service.py
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import logging

from src.core.entities.portfolio import Portfolio
from src.infrastructure.repositories.price_history_repository import PriceHistoryRepository

logger = logging.getLogger(__name__)


class PortfolioSnapshotService:
    """Generates daily snapshots of portfolio value."""

    def __init__(self, price_repo: PriceHistoryRepository):
        self.price_repo = price_repo

    def generate_daily_snapshots(self, portfolio: Portfolio) -> List[Dict]:
        """Generate daily snapshots from first transaction to today."""
        snapshots = []

        # Get date range
        if not portfolio.transactions:
            return snapshots

        start_date = min(tx.timestamp.date() for tx in portfolio.transactions)
        end_date = date.today()

        # Track running positions
        positions = {}  # asset -> amount
        cash_balance = Decimal('0')

        # Sort transactions by timestamp
        sorted_txs = sorted(portfolio.transactions, key=lambda x: x.timestamp)
        tx_index = 0

        # Generate snapshot for each day
        current_date = start_date
        while current_date <= end_date:
            # Apply transactions for this day
            while tx_index < len(sorted_txs) and sorted_txs[tx_index].timestamp.date() <= current_date:
                tx = sorted_txs[tx_index]

                # Update positions based on transaction type
                if tx.type.value == 'Deposit':
                    cash_balance += tx.amount
                elif tx.type.value == 'Withdrawal':
                    cash_balance -= tx.amount
                elif tx.type.value == 'Buy':
                    positions[tx.asset] = positions.get(tx.asset, Decimal('0')) + tx.amount
                    cash_balance -= tx.total_usd or Decimal('0')
                elif tx.type.value == 'Sell':
                    positions[tx.asset] = positions.get(tx.asset, Decimal('0')) - tx.amount
                    cash_balance += tx.total_usd or Decimal('0')
                elif tx.type.value == 'Convert (from)':
                    positions[tx.asset] = positions.get(tx.asset, Decimal('0')) - tx.amount
                elif tx.type.value == 'Convert (to)':
                    positions[tx.asset] = positions.get(tx.asset, Decimal('0')) + tx.amount
                elif tx.type.value in ['Send', 'Receive']:
                    # Transfers between wallets
                    if tx.type.value == 'Send':
                        positions[tx.asset] = positions.get(tx.asset, Decimal('0')) - tx.amount
                    else:
                        positions[tx.asset] = positions.get(tx.asset, Decimal('0')) + tx.amount

                tx_index += 1

            # Calculate portfolio value for this day
            total_value = cash_balance

            # Add crypto values
            for asset, amount in positions.items():
                if amount > 0 and asset != 'USD':
                    price = self.price_repo.get_price(asset, current_date)
                    if price:
                        total_value += amount * price
                    else:
                        # Use last known price
                        logger.warning(f"No price for {asset} on {current_date}")

            snapshots.append({
                'date': current_date,
                'total_value': float(total_value),
                'cash_balance': float(cash_balance),
                'positions': {
                    asset: float(amount)
                    for asset, amount in positions.items()
                    if amount > 0
                }
            })

            current_date += timedelta(days=1)

        return snapshots
