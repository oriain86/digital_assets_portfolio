# src/core/entities/position.py

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Tuple
from datetime import datetime
import heapq

from .transaction import Transaction, TransactionType


@dataclass
class CostBasisLot:
    """Represents a single lot for cost basis tracking (FIFO/LIFO/etc)."""
    amount: Decimal
    cost_per_unit: Decimal
    acquisition_date: datetime
    transaction_id: str

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost of this lot."""
        return self.amount * self.cost_per_unit

    def __lt__(self, other):
        """Comparison for heap operations (FIFO by default)."""
        return self.acquisition_date < other.acquisition_date


@dataclass
class Position:
    """
    Represents a position in a specific asset with complete tracking of:
    - Current holdings
    - Cost basis using various accounting methods
    - Realized and unrealized gains/losses
    - Transaction history
    """

    asset: str
    current_amount: Decimal = Decimal('0')
    current_price: Optional[Decimal] = None

    # Cost basis tracking
    cost_basis_lots: List[CostBasisLot] = field(default_factory=list)
    total_cost_basis: Decimal = Decimal('0')

    # P&L tracking
    realized_gains: Decimal = Decimal('0')
    realized_losses: Decimal = Decimal('0')

    # Transaction history
    transactions: List[Transaction] = field(default_factory=list)

    # Statistics
    total_bought: Decimal = Decimal('0')
    total_sold: Decimal = Decimal('0')
    total_fees: Decimal = Decimal('0')

    def add_transaction(self, transaction: Transaction,
                        cost_basis_method: str = 'FIFO') -> Optional[Decimal]:
        """
        Process a transaction and update position accordingly.
        Returns realized gain/loss if applicable.
        """
        if transaction.asset != self.asset:
            raise ValueError(f"Transaction asset {transaction.asset} doesn't match position asset {self.asset}")

        self.transactions.append(transaction)
        realized_gain_loss = None

        # Handle different transaction types
        if transaction.type.is_acquisition():
            self._process_acquisition(transaction)
        elif transaction.type.is_disposal():
            realized_gain_loss = self._process_disposal(transaction, cost_basis_method)

        # Update statistics
        if transaction.fee_usd:
            self.total_fees += transaction.fee_usd

        return realized_gain_loss

    def _process_acquisition(self, transaction: Transaction):
        """Process an acquisition (buy, receive, etc.)."""
        # Update current amount
        self.current_amount += transaction.amount

        # Add to cost basis lots
        cost_per_unit = transaction.get_effective_price()
        lot = CostBasisLot(
            amount=transaction.amount,
            cost_per_unit=cost_per_unit,
            acquisition_date=transaction.timestamp,
            transaction_id=transaction.transaction_id
        )
        self.cost_basis_lots.append(lot)

        # Update total cost basis
        self.total_cost_basis += lot.total_cost

        # Update statistics
        if transaction.type == TransactionType.BUY:
            self.total_bought += transaction.amount

    def _process_disposal(self, transaction: Transaction,
                          cost_basis_method: str = 'FIFO') -> Decimal:
        """Process a disposal (sell, send, etc.) and calculate realized gains."""
        if transaction.amount > self.current_amount:
            raise ValueError(
                f"Insufficient balance: trying to dispose {transaction.amount} but only have {self.current_amount}")

        # Update current amount
        self.current_amount -= transaction.amount

        # Calculate cost basis and realized gains
        disposed_cost = Decimal('0')
        remaining_to_dispose = transaction.amount

        if cost_basis_method == 'FIFO':
            disposed_cost = self._dispose_fifo(remaining_to_dispose)
        elif cost_basis_method == 'LIFO':
            disposed_cost = self._dispose_lifo(remaining_to_dispose)
        elif cost_basis_method == 'HIFO':
            disposed_cost = self._dispose_hifo(remaining_to_dispose)
        else:
            raise ValueError(f"Unsupported cost basis method: {cost_basis_method}")

        # Calculate realized gain/loss
        proceeds = transaction.get_effective_cost()
        realized_gain_loss = proceeds - disposed_cost

        # Update realized gains/losses
        if realized_gain_loss > 0:
            self.realized_gains += realized_gain_loss
        else:
            self.realized_losses += abs(realized_gain_loss)

        # Update statistics
        if transaction.type == TransactionType.SELL:
            self.total_sold += transaction.amount

        # Update total cost basis
        self.total_cost_basis -= disposed_cost

        return realized_gain_loss

    def _dispose_fifo(self, amount: Decimal) -> Decimal:
        """Dispose using First-In-First-Out method."""
        disposed_cost = Decimal('0')
        remaining = amount
        new_lots = []

        # Sort lots by acquisition date (oldest first)
        self.cost_basis_lots.sort(key=lambda x: x.acquisition_date)

        for lot in self.cost_basis_lots:
            if remaining <= 0:
                new_lots.append(lot)
            elif lot.amount <= remaining:
                # Dispose entire lot
                disposed_cost += lot.total_cost
                remaining -= lot.amount
            else:
                # Dispose partial lot
                disposed_amount = remaining
                disposed_cost += disposed_amount * lot.cost_per_unit

                # Keep remaining portion
                new_lot = CostBasisLot(
                    amount=lot.amount - disposed_amount,
                    cost_per_unit=lot.cost_per_unit,
                    acquisition_date=lot.acquisition_date,
                    transaction_id=lot.transaction_id
                )
                new_lots.append(new_lot)
                remaining = Decimal('0')

        self.cost_basis_lots = new_lots
        return disposed_cost

    def _dispose_lifo(self, amount: Decimal) -> Decimal:
        """Dispose using Last-In-First-Out method."""
        disposed_cost = Decimal('0')
        remaining = amount
        new_lots = []

        # Sort lots by acquisition date (newest first)
        self.cost_basis_lots.sort(key=lambda x: x.acquisition_date, reverse=True)

        for lot in self.cost_basis_lots:
            if remaining <= 0:
                new_lots.append(lot)
            elif lot.amount <= remaining:
                # Dispose entire lot
                disposed_cost += lot.total_cost
                remaining -= lot.amount
            else:
                # Dispose partial lot
                disposed_amount = remaining
                disposed_cost += disposed_amount * lot.cost_per_unit

                # Keep remaining portion
                new_lot = CostBasisLot(
                    amount=lot.amount - disposed_amount,
                    cost_per_unit=lot.cost_per_unit,
                    acquisition_date=lot.acquisition_date,
                    transaction_id=lot.transaction_id
                )
                new_lots.append(new_lot)
                remaining = Decimal('0')

        self.cost_basis_lots = new_lots
        return disposed_cost

    def _dispose_hifo(self, amount: Decimal) -> Decimal:
        """Dispose using Highest-In-First-Out method."""
        disposed_cost = Decimal('0')
        remaining = amount
        new_lots = []

        # Sort lots by cost per unit (highest first)
        self.cost_basis_lots.sort(key=lambda x: x.cost_per_unit, reverse=True)

        for lot in self.cost_basis_lots:
            if remaining <= 0:
                new_lots.append(lot)
            elif lot.amount <= remaining:
                # Dispose entire lot
                disposed_cost += lot.total_cost
                remaining -= lot.amount
            else:
                # Dispose partial lot
                disposed_amount = remaining
                disposed_cost += disposed_amount * lot.cost_per_unit

                # Keep remaining portion
                new_lot = CostBasisLot(
                    amount=lot.amount - disposed_amount,
                    cost_per_unit=lot.cost_per_unit,
                    acquisition_date=lot.acquisition_date,
                    transaction_id=lot.transaction_id
                )
                new_lots.append(new_lot)
                remaining = Decimal('0')

        self.cost_basis_lots = new_lots
        return disposed_cost

    def get_average_cost(self) -> Decimal:
        """Calculate average cost per unit."""
        if self.current_amount == 0:
            return Decimal('0')
        return self.total_cost_basis / self.current_amount

    def get_current_value(self) -> Decimal:
        """Get current market value of position."""
        if not self.current_price:
            return Decimal('0')
        return self.current_amount * self.current_price

    def get_unrealized_pnl(self) -> Decimal:
        """Calculate unrealized profit/loss."""
        return self.get_current_value() - self.total_cost_basis

    def get_unrealized_pnl_percent(self) -> Decimal:
        """Calculate unrealized profit/loss percentage."""
        if self.total_cost_basis == 0:
            return Decimal('0')
        return (self.get_unrealized_pnl() / self.total_cost_basis) * 100

    def get_total_realized_pnl(self) -> Decimal:
        """Get total realized profit/loss."""
        return self.realized_gains - self.realized_losses

    def is_closed(self) -> bool:
        """Check if position is closed (no current holdings)."""
        return self.current_amount == 0

    def get_holding_period_days(self) -> int:
        """Get days since first acquisition (for open positions)."""
        if not self.cost_basis_lots:
            return 0

        oldest_lot = min(self.cost_basis_lots, key=lambda x: x.acquisition_date)
        return (datetime.now() - oldest_lot.acquisition_date).days

    def to_dict(self) -> dict:
        """Convert position to dictionary for reporting."""
        return {
            'asset': self.asset,
            'amount': float(self.current_amount),
            'avg_cost': float(self.get_average_cost()),
            'current_price': float(self.current_price) if self.current_price else None,
            'total_cost': float(self.total_cost_basis),
            'current_value': float(self.get_current_value()),
            'unrealized_pnl': float(self.get_unrealized_pnl()),
            'unrealized_pnl_percent': float(self.get_unrealized_pnl_percent()),
            'realized_gains': float(self.realized_gains),
            'realized_losses': float(self.realized_losses),
            'total_realized_pnl': float(self.get_total_realized_pnl()),
            'total_bought': float(self.total_bought),
            'total_sold': float(self.total_sold),
            'total_fees': float(self.total_fees),
            'is_closed': self.is_closed(),
            'holding_period_days': self.get_holding_period_days(),
            'num_transactions': len(self.transactions),
            'num_lots': len(self.cost_basis_lots)
        }
