
from datetime import datetime
from decimal import Decimal
from src.core.entities.transaction import Transaction, TransactionType


def create_sample_transactions():
    """Create sample transactions for testing."""
    return [
        Transaction(
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            type=TransactionType.DEPOSIT,
            asset="USD",
            amount=Decimal("10000")
        ),
        Transaction(
            timestamp=datetime(2024, 1, 2, 10, 0, 0),
            type=TransactionType.BUY,
            asset="BTC",
            amount=Decimal("0.5"),
            price_usd=Decimal("40000"),
            fee_usd=Decimal("20")
        ),
        Transaction(
            timestamp=datetime(2024, 1, 3, 10, 0, 0),
            type=TransactionType.BUY,
            asset="ETH",
            amount=Decimal("5"),
            price_usd=Decimal("2000"),
            fee_usd=Decimal("10")
        ),
    ]


def create_sample_portfolio():
    """Create sample portfolio for testing."""
    from src.core.entities.portfolio import Portfolio

    portfolio = Portfolio(name="Test Portfolio")

    for tx in create_sample_transactions():
        portfolio.process_transaction(tx)

    return portfolio
