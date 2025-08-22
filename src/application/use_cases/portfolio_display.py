# src/application/use_cases/portfolio_display.py

from typing import Dict, Any
from decimal import Decimal
from src.application.services.portfolio_service import PortfolioService
from src.application.use_cases.calculate_metrics import CalculateMetricsUseCase


class PortfolioDisplayUseCase:
    """Use case for displaying portfolio information."""

    def __init__(self, portfolio_service: PortfolioService):
        self.portfolio_service = portfolio_service
        self.metrics_calculator = CalculateMetricsUseCase()

    def show_summary(self):
        """Display portfolio summary with corrected metrics."""
        portfolio = self.portfolio_service.portfolio

        # Calculate metrics
        metrics_result = self.metrics_calculator.execute(portfolio)

        if not metrics_result['success']:
            print("❌ Failed to calculate metrics")
            return

        performance = metrics_result['performance']
        risk = metrics_result['risk']
        trading = metrics_result['trading']

        current_value = performance['current_value']

        print("\n📈 Portfolio Performance Summary")
        print("─" * 50)
        print(f"Current Value:    ${current_value:,.2f}")
        print(f"Net Profit:       ${performance['net_profit']:,.2f} (after fees)")

        print("\n📊 Performance Metrics")
        print("─" * 50)
        print(f"Annual Return:    {performance['annualized_return']:.1f}%")
        print(f"Sharpe Ratio:     {risk['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio:    {risk['sortino_ratio']:.2f}")
        print(f"Max Drawdown:     {risk['max_drawdown']:.1f}%")
        print(f"Win Rate:         {trading['win_rate']:.1f}%")
