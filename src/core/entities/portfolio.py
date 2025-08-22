# src/core/entities/portfolio.py

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

from .transaction import Transaction, TransactionType
from .position import Position


@dataclass
class PortfolioSnapshot:
    """Represents portfolio state at a specific point in time."""
    timestamp: datetime
    total_value: Decimal
    positions: Dict[str, Dict]  # Asset -> position data
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    cash_balance: Decimal


@dataclass
class PortfolioMetrics:
    """Container for portfolio performance metrics."""
    total_return: Decimal
    total_return_percent: Decimal
    realized_gains: Decimal
    realized_losses: Decimal
    unrealized_pnl: Decimal
    total_fees: Decimal

    # Risk metrics
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    max_drawdown_duration: Optional[int] = None
    volatility: Optional[float] = None
    calmar_ratio: Optional[float] = None

    # Additional metrics
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    avg_win: Optional[Decimal] = None
    avg_loss: Optional[Decimal] = None
    best_trade: Optional[Decimal] = None
    worst_trade: Optional[Decimal] = None

    # Time-based metrics
    cagr: Optional[float] = None
    time_in_market: Optional[float] = None


@dataclass
class Portfolio:
    """
    Main portfolio entity that manages all positions and tracks overall performance.

    This class orchestrates the interaction between transactions and positions,
    maintains portfolio history, and calculates comprehensive metrics.
    """

    name: str = "Crypto Portfolio"
    base_currency: str = "USD"
    cost_basis_method: str = "FIFO"

    # Positions tracking
    positions: Dict[str, Position] = field(default_factory=dict)
    closed_positions: List[Position] = field(default_factory=list)

    # Cash tracking
    cash_balance: Decimal = Decimal('0')
    cash_transactions: List[Transaction] = field(default_factory=list)

    # Portfolio history
    snapshots: List[PortfolioSnapshot] = field(default_factory=list)
    daily_returns: List[Tuple[datetime, float]] = field(default_factory=list)

    # Aggregate tracking
    total_deposits: Decimal = Decimal('0')
    total_withdrawals: Decimal = Decimal('0')
    total_fees: Decimal = Decimal('0')

    def process_transaction(self, transaction: Transaction) -> Optional[Decimal]:
        """
        Process a transaction and update portfolio state.
        Returns realized gain/loss if applicable.
        """
        realized_pnl = None

        # Handle deposits and withdrawals
        if transaction.type == TransactionType.DEPOSIT:
            self._process_deposit(transaction)
        elif transaction.type == TransactionType.WITHDRAWAL:
            self._process_withdrawal(transaction)
        else:
            # Get or create position
            position = self._get_or_create_position(transaction.asset)

            # Process the transaction
            realized_pnl = position.add_transaction(transaction, self.cost_basis_method)

            # Handle conversions
            if transaction.type in [TransactionType.CONVERT_FROM, TransactionType.CONVERT_TO]:
                self._process_conversion(transaction)

            # Check if position is closed
            if position.is_closed() and position.asset != self.base_currency:
                self.closed_positions.append(position)
                del self.positions[position.asset]

        # Update total fees
        if transaction.fee_usd:
            self.total_fees += transaction.fee_usd

        return realized_pnl

    def _get_or_create_position(self, asset: str) -> Position:
        """Get existing position or create new one."""
        if asset not in self.positions:
            self.positions[asset] = Position(asset=asset)
        return self.positions[asset]

    def _process_deposit(self, transaction: Transaction):
        """Process cash deposit."""
        if transaction.asset == self.base_currency:
            self.cash_balance += transaction.amount
            self.total_deposits += transaction.amount
            self.cash_transactions.append(transaction)
        else:
            # Non-cash deposit, treat as regular acquisition
            position = self._get_or_create_position(transaction.asset)
            position.add_transaction(transaction, self.cost_basis_method)

    def _process_withdrawal(self, transaction: Transaction):
        """Process cash withdrawal."""
        if transaction.asset == self.base_currency:
            self.cash_balance -= transaction.amount
            self.total_withdrawals += transaction.amount
            self.cash_transactions.append(transaction)
        else:
            # Non-cash withdrawal, treat as regular disposal
            position = self._get_or_create_position(transaction.asset)
            position.add_transaction(transaction, self.cost_basis_method)

    def _process_conversion(self, transaction: Transaction):
        """Handle conversion transactions."""
        # Conversions are typically paired (convert from X to Y)
        # The actual pairing logic would be handled at a higher level
        pass

    def update_prices(self, prices: Dict[str, Decimal]):
        """Update current prices for all positions."""
        for asset, price in prices.items():
            if asset in self.positions:
                self.positions[asset].current_price = price

    def take_snapshot(self, timestamp: Optional[datetime] = None):
        """Take a snapshot of current portfolio state."""
        if timestamp is None:
            timestamp = datetime.now()

        # Calculate current values
        total_value = self.cash_balance
        positions_data = {}
        unrealized_pnl = Decimal('0')

        for asset, position in self.positions.items():
            position_data = position.to_dict()
            positions_data[asset] = position_data

            if asset != self.base_currency:
                total_value += position.get_current_value()
                unrealized_pnl += position.get_unrealized_pnl()

        # Calculate realized P&L
        realized_pnl = sum(p.get_total_realized_pnl() for p in self.positions.values())
        realized_pnl += sum(p.get_total_realized_pnl() for p in self.closed_positions)

        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            total_value=total_value,
            positions=positions_data,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            cash_balance=self.cash_balance
        )

        self.snapshots.append(snapshot)

        # Update daily returns if we have previous snapshot
        if len(self.snapshots) > 1:
            prev_snapshot = self.snapshots[-2]
            if prev_snapshot.total_value > 0:
                daily_return = float((snapshot.total_value - prev_snapshot.total_value) / prev_snapshot.total_value)
                self.daily_returns.append((timestamp, daily_return))

    def calculate_metrics(self, risk_free_rate: float = 0.02) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics."""
        # Basic P&L metrics
        total_realized_gains = sum(p.realized_gains for p in self.positions.values())
        total_realized_gains += sum(p.realized_gains for p in self.closed_positions)

        total_realized_losses = sum(p.realized_losses for p in self.positions.values())
        total_realized_losses += sum(p.realized_losses for p in self.closed_positions)

        total_unrealized_pnl = sum(p.get_unrealized_pnl() for p in self.positions.values()
                                   if p.asset != self.base_currency)

        # Net invested (deposits - withdrawals)
        net_invested = self.total_deposits - self.total_withdrawals

        # Current portfolio value
        current_value = self.get_total_value()

        # Total return
        total_return = current_value - net_invested
        total_return_percent = (total_return / net_invested * 100) if net_invested > 0 else Decimal('0')

        metrics = PortfolioMetrics(
            total_return=total_return,
            total_return_percent=total_return_percent,
            realized_gains=total_realized_gains,
            realized_losses=total_realized_losses,
            unrealized_pnl=total_unrealized_pnl,
            total_fees=self.total_fees
        )

        # Calculate risk metrics if we have enough data
        if len(self.daily_returns) > 30:
            returns = [r[1] for r in self.daily_returns]

            # Volatility (annualized)
            metrics.volatility = np.std(returns) * np.sqrt(252)

            # Sharpe ratio
            excess_returns = [r - risk_free_rate / 252 for r in returns]
            if metrics.volatility > 0:
                metrics.sharpe_ratio = np.mean(excess_returns) * 252 / metrics.volatility

            # Sortino ratio (downside deviation)
            downside_returns = [r for r in excess_returns if r < 0]
            if downside_returns:
                downside_std = np.std(downside_returns) * np.sqrt(252)
                if downside_std > 0:
                    metrics.sortino_ratio = np.mean(excess_returns) * 252 / downside_std

            # Maximum drawdown
            metrics.max_drawdown, metrics.max_drawdown_duration = self._calculate_max_drawdown()

            # Calmar ratio
            if metrics.max_drawdown and metrics.max_drawdown < 0:
                annual_return = np.mean(returns) * 252
                metrics.calmar_ratio = annual_return / abs(metrics.max_drawdown)

            # Win rate and profit factor
            winning_trades = [pnl for pnl in self._get_all_realized_trades() if pnl > 0]
            losing_trades = [pnl for pnl in self._get_all_realized_trades() if pnl < 0]

            if winning_trades or losing_trades:
                metrics.win_rate = len(winning_trades) / (len(winning_trades) + len(losing_trades))

                if winning_trades:
                    metrics.avg_win = Decimal(str(np.mean([float(w) for w in winning_trades])))
                    metrics.best_trade = max(winning_trades)

                if losing_trades:
                    metrics.avg_loss = Decimal(str(np.mean([float(l) for l in losing_trades])))
                    metrics.worst_trade = min(losing_trades)

                    total_wins = sum(winning_trades)
                    total_losses = abs(sum(losing_trades))
                    if total_losses > 0:
                        metrics.profit_factor = float(total_wins / total_losses)

        return metrics

    def _calculate_max_drawdown(self) -> Tuple[Optional[float], Optional[int]]:
        """Calculate maximum drawdown and duration."""
        if len(self.snapshots) < 2:
            return None, None

        values = [float(s.total_value) for s in self.snapshots]

        peak = values[0]
        max_dd = 0
        max_dd_duration = 0
        current_dd_start = 0

        for i, value in enumerate(values):
            if value > peak:
                peak = value
                current_dd_start = i

            dd = (value - peak) / peak
            if dd < max_dd:
                max_dd = dd
                max_dd_duration = i - current_dd_start

        return max_dd, max_dd_duration

    def _get_all_realized_trades(self) -> List[Decimal]:
        """Get all realized P&L from trades."""
        trades = []

        for position in list(self.positions.values()) + self.closed_positions:
            for transaction in position.transactions:
                if transaction.realized_gain_loss is not None:
                    trades.append(transaction.realized_gain_loss)

        return trades

    def get_total_value(self) -> Decimal:
        """Get current total portfolio value."""
        total = self.cash_balance

        for position in self.positions.values():
            if position.asset != self.base_currency:
                total += position.get_current_value()

        return total

    def get_asset_allocation(self) -> Dict[str, float]:
        """Get current asset allocation percentages."""
        total_value = self.get_total_value()
        if total_value == 0:
            return {}

        allocation = {}

        # Cash allocation
        if self.cash_balance > 0:
            allocation[self.base_currency] = float(self.cash_balance / total_value * 100)

        # Asset allocations
        for asset, position in self.positions.items():
            if asset != self.base_currency and position.current_amount > 0:
                value = position.get_current_value()
                allocation[asset] = float(value / total_value * 100)

        return allocation

    def get_performance_by_period(self, period: str = 'monthly') -> List[Dict]:
        """Get performance aggregated by period (daily, weekly, monthly, yearly)."""
        if not self.snapshots:
            return []

        # Group snapshots by period
        period_data = defaultdict(list)

        for snapshot in self.snapshots:
            if period == 'daily':
                key = snapshot.timestamp.date()
            elif period == 'weekly':
                key = snapshot.timestamp.isocalendar()[:2]  # (year, week)
            elif period == 'monthly':
                key = (snapshot.timestamp.year, snapshot.timestamp.month)
            elif period == 'yearly':
                key = snapshot.timestamp.year
            else:
                raise ValueError(f"Invalid period: {period}")

            period_data[key].append(snapshot)

        # Calculate returns for each period
        results = []
        sorted_periods = sorted(period_data.keys())

        for i, period_key in enumerate(sorted_periods):
            period_snapshots = period_data[period_key]

            # Get first and last snapshot of period
            first_snapshot = period_snapshots[0]
            last_snapshot = period_snapshots[-1]

            # Calculate return
            if i > 0:
                prev_period_snapshots = period_data[sorted_periods[i - 1]]
                prev_last_snapshot = prev_period_snapshots[-1]

                if prev_last_snapshot.total_value > 0:
                    period_return = float(
                        (last_snapshot.total_value - prev_last_snapshot.total_value) /
                        prev_last_snapshot.total_value * 100
                    )
                else:
                    period_return = 0.0
            else:
                period_return = 0.0

            results.append({
                'period': period_key,
                'start_value': float(first_snapshot.total_value),
                'end_value': float(last_snapshot.total_value),
                'return_percent': period_return,
                'realized_pnl': float(last_snapshot.realized_pnl),
                'unrealized_pnl': float(last_snapshot.unrealized_pnl)
            })

        return results
