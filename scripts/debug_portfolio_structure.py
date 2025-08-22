# scripts/debug_portfolio_structure.py

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.application.services.portfolio_service import PortfolioService


def debug_portfolio_structure():
    """Debug the portfolio structure."""

    print("=== Loading Portfolio ===")
    portfolio_service = PortfolioService()
    portfolio_service.load_portfolio()

    portfolio = portfolio_service.portfolio

    print(f"\nPortfolio attributes: {dir(portfolio)}")

    print(f"\nNumber of positions: {len(portfolio.positions)}")

    # Check first position
    if portfolio.positions:
        first_asset = list(portfolio.positions.keys())[0]
        first_position = portfolio.positions[first_asset]

        print(f"\nFirst position ({first_asset}) attributes: {dir(first_position)}")
        print(f"Current value: {first_position.current_value}")
        print(f"Cost basis: {first_position.cost_basis}")

    # Check for cash balance
    if hasattr(portfolio, 'cash_balance'):
        print(f"\nCash balance: {portfolio.cash_balance}")

    # Check cash transactions
    print(f"\nCash transactions: {len(portfolio.cash_transactions)}")
    if portfolio.cash_transactions:
        print(f"First cash transaction: {portfolio.cash_transactions[0]}")


if __name__ == "__main__":
    debug_portfolio_structure()
