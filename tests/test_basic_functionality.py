# tests/test_basic_functionality.py

import pytest
from decimal import Decimal
from datetime import datetime

from src.core.entities.transaction import Transaction, TransactionType
from src.core.entities.position import Position
from src.core.entities.portfolio import Portfolio
from src.application.services.metrics_calculator import MetricsCalculator


class TestBasicFunctionality:
    """Test basic functionality of the portfolio tracker."""

    def test_create_transaction(self):
        """Test creating a transaction."""
        tx = Transaction(
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            type=TransactionType.BUY,
            asset="BTC",
            amount=Decimal("0.1"),
            price_usd=Decimal("45000"),
            total_usd=Decimal("4500"),
            fee_usd=Decimal("10"),
            exchange="Coinbase",
            transaction_id="test_001"
        )

        assert tx.asset == "BTC"
        assert tx.amount == Decimal("0.1")
        assert tx.get_effective_cost() == Decimal("4510")  # Including fee

    def test_position_tracking(self):
        """Test position tracking with FIFO."""
        position = Position(asset="ETH")

        # First buy
        tx1 = Transaction(
            timestamp=datetime(2024, 1, 1),
            type=TransactionType.BUY,
            asset="ETH",
            amount=Decimal("1"),
            price_usd=Decimal("2000"),
            fee_usd=Decimal("5")
        )
        position.add_transaction(tx1)

        assert position.current_amount == Decimal("1")
        assert position.total_cost_basis == Decimal("2005")  # Including fee

        # Second buy at different price
        tx2 = Transaction(
            timestamp=datetime(2024, 1, 2),
            type=TransactionType.BUY,
            asset="ETH",
            amount=Decimal("1"),
            price_usd=Decimal("2500"),
            fee_usd=Decimal("5")
        )
        position.add_transaction(tx2)

        assert position.current_amount == Decimal("2")
        assert position.total_cost_basis == Decimal("4510")
        assert position.get_average_cost() == Decimal("2255")

        # Sell using FIFO
        tx3 = Transaction(
            timestamp=datetime(2024, 1, 3),
            type=TransactionType.SELL,
            asset="ETH",
            amount=Decimal("0.5"),
            price_usd=Decimal("3000"),
            fee_usd=Decimal("5")
        )
        realized_pnl = position.add_transaction(tx3, cost_basis_method='FIFO')

        # Should sell from first lot (cost basis 2005 per ETH)
        # Proceeds: 0.5 * 3000 - 5 = 1495
        # Cost basis: 0.5 * 2005 = 1002.5
        # Realized P&L: 1495 - 1002.5 = 492.5
        assert realized_pnl == Decimal("492.5")
        assert position.current_amount == Decimal("1.5")

    def test_portfolio_management(self):
        """Test portfolio-level operations."""
        portfolio = Portfolio(name="Test Portfolio", cost_basis_method="FIFO")

        # Deposit cash
        deposit = Transaction(
            timestamp=datetime(2024, 1, 1),
            type=TransactionType.DEPOSIT,
            asset="USD",
            amount=Decimal("10000")
        )
        portfolio.process_transaction(deposit)

        assert portfolio.cash_balance == Decimal("10000")
        assert portfolio.total_deposits == Decimal("10000")

        # Buy BTC
        buy_btc = Transaction(
            timestamp=datetime(2024, 1, 2),
            type=TransactionType.BUY,
            asset="BTC",
            amount=Decimal("0.2"),
            price_usd=Decimal("40000"),
            total_usd=Decimal("8000"),
            fee_usd=Decimal("20")
        )
        portfolio.process_transaction(buy_btc)

        assert "BTC" in portfolio.positions
        assert portfolio.positions["BTC"].current_amount == Decimal("0.2")

        # Update prices
        portfolio.update_prices({"BTC": Decimal("45000")})

        # Check unrealized P&L
        btc_position = portfolio.positions["BTC"]
        unrealized_pnl = btc_position.get_unrealized_pnl()

        # Current value: 0.2 * 45000 = 9000
        # Cost basis: 8020 (including fee)
        # Unrealized P&L: 9000 - 8020 = 980
        assert unrealized_pnl == Decimal("980")

    def test_metrics_calculation(self):
        """Test basic metrics calculation."""
        portfolio = Portfolio(name="Test Portfolio")
        calculator = MetricsCalculator()

        # Add some sample transactions
        transactions = [
            Transaction(
                timestamp=datetime(2024, 1, 1),
                type=TransactionType.DEPOSIT,
                asset="USD",
                amount=Decimal("10000")
            ),
            Transaction(
                timestamp=datetime(2024, 1, 2),
                type=TransactionType.BUY,
                asset="SOL",
                amount=Decimal("100"),
                price_usd=Decimal("50"),
                fee_usd=Decimal("10")
            )
        ]

        for tx in transactions:
            portfolio.process_transaction(tx)

        # Update price
        portfolio.update_prices({"SOL": Decimal("60")})

        # Take snapshot
        portfolio.take_snapshot()

        # Calculate metrics
        metrics = calculator.calculate_portfolio_metrics(portfolio)

        assert 'basic' in metrics
        assert metrics['basic']['total_fees'] == 10.0


# Run tests
if __name__ == "__main__":
    test = TestBasicFunctionality()
    test.test_create_transaction()
    test.test_position_tracking()
    test.test_portfolio_management()
    test.test_metrics_calculation()
    print("All tests passed!")
