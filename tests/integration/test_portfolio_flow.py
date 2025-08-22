
import pytest
from datetime import datetime
from decimal import Decimal

from src.core.entities.portfolio import Portfolio
from src.core.entities.transaction import Transaction, TransactionType
from src.application.services.portfolio_service import PortfolioService
from tests.fixtures.sample_data import create_sample_transactions


class TestPortfolioFlow:
    """Test complete portfolio workflow."""

    def test_full_portfolio_lifecycle(self, tmp_path):
        """Test creating, updating, and analyzing a portfolio."""
        # Create portfolio service with temp directory
        service = PortfolioService(
            data_path=str(tmp_path / "data"),
            cache_path=str(tmp_path / "cache")
        )

        # Create and save portfolio
        portfolio = Portfolio(name="Test Portfolio")

        # Add transactions
        for tx in create_sample_transactions():
            portfolio.process_transaction(tx)

        # Save portfolio
        service.portfolio = portfolio
        service._save_portfolio_state()

        # Load portfolio
        assert service.load_portfolio()
        loaded_portfolio = service.get_portfolio()

        # Verify loaded data
        assert loaded_portfolio.name == "Test Portfolio"
        assert "BTC" in loaded_portfolio.positions
        assert "ETH" in loaded_portfolio.positions

        # Update prices
        loaded_portfolio.update_prices({
            "BTC": Decimal("45000"),
            "ETH": Decimal("2500")
        })

        # Calculate metrics
        metrics = service.get_portfolio_metrics()

        assert 'basic' in metrics
        assert metrics['basic']['total_fees'] > 0
