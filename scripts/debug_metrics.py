# scripts/debug_metrics_fixed.py

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from datetime import date
from src.application.services.portfolio_service import PortfolioService
from src.application.services.metrics_calculator import MetricsCalculator
from src.infrastructure.repositories.price_history_repository import PriceHistoryRepository


def debug_metrics():
    """Debug metrics calculation with proper method calls."""

    print("=== Loading Portfolio ===")
    portfolio_service = PortfolioService()
    portfolio_service.load_portfolio()

    portfolio = portfolio_service.portfolio

    # Get all transactions
    all_transactions = []
    for position in portfolio.positions.values():
        all_transactions.extend(position.transactions)
    all_transactions.extend(portfolio.cash_transactions)

    print(f"Total positions: {len(portfolio.positions)}")
    print(f"Total transactions: {len(all_transactions)}")

    if all_transactions:
        tx_dates = [tx.timestamp.date() for tx in all_transactions]
        print(f"Transaction date range: {min(tx_dates)} to {max(tx_dates)}")

    # Show current portfolio value
    print("\n=== Current Portfolio Value ===")
    total_value = portfolio.cash_balance
    for asset, position in portfolio.positions.items():
        value = position.get_current_value()
        total_value += value
        print(f"{asset}: ${value:,.2f} ({position.current_amount} @ ${position.current_price})")
    print(f"Cash: ${portfolio.cash_balance:,.2f}")
    print(f"Total: ${total_value:,.2f}")

    print("\n=== Checking Price Data ===")
    price_repo = PriceHistoryRepository()

    # Test with a date we know exists
    test_date = date(2024, 8, 1)  # Try August 1st instead
    btc_price = price_repo.get_price('BTC', test_date)
    print(f"BTC price on {test_date}: ${btc_price}")

    print("\n=== Calculating Metrics ===")
    calculator = MetricsCalculator()
    metrics = calculator.calculate_metrics(portfolio)

    print(f"\nCalculated metrics:")
    for key, value in metrics.items():
        if key != 'time_series':
            print(f"- {key}: {value}")

    if 'time_series' in metrics:
        ts = metrics['time_series']
        print(f"\nTime series:")
        print(f"- Days: {len(ts.get('dates', []))}")
        if ts.get('dates'):
            print(f"- Date range: {ts['dates'][0]} to {ts['dates'][-1]}")
            if ts.get('values'):
                print(f"- First value: ${ts['values'][0]:,.2f}")
                print(f"- Last value: ${ts['values'][-1]:,.2f}")


if __name__ == "__main__":
    debug_metrics()
