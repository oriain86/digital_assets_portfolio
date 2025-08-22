# src/application/use_cases/portfolio_initialization.py

from typing import Dict, Any, List
from src.application.services.portfolio_service import PortfolioService
from src.application.services.transaction_processor import TransactionProcessor


class PortfolioInitializationUseCase:
    """Use case for initializing a portfolio from CSV."""

    def __init__(self, portfolio_service: PortfolioService):
        self.portfolio_service = portfolio_service
        self.transaction_processor = TransactionProcessor()

    def execute(self, csv_path: str) -> Dict[str, Any]:
        """Initialize portfolio from CSV file."""
        print("\n📊 Initializing portfolio from CSV...")
        print(f"   File: {csv_path}")
        print(f"   Method: {self.portfolio_service.cost_basis_method}")

        try:
            result = self.portfolio_service.initialize_portfolio(csv_path)

            if result['success']:
                self._print_success_summary(result['summary'])
                self._print_warnings(result)

            return result

        except Exception as e:
            print(f"\n❌ Error initializing portfolio: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _print_success_summary(self, summary: Dict[str, Any]):
        """Print initialization success summary."""
        print("\n✅ Portfolio initialized successfully!")
        print(f"   • Total transactions: {summary['total_transactions']:,}")
        print(f"   • Transactions processed: {summary['processed']:,}")
        print(f"   • Current positions: {summary['current_positions']}")
        print(f"   • Portfolio value: ${summary['total_value']:,.2f}")
        print(f"   • Net invested: ${summary['net_invested']:,.2f}")

    def _print_warnings(self, result: Dict[str, Any]):
        """Print any warnings from initialization."""
        if result.get('errors'):
            print(f"\n⚠️  Warning: {len(result['errors'])} transaction errors occurred")
            print("   First few errors:")
            for error in result['errors'][:3]:
                print(f"   • {error.get('error', str(error))}")

        if result.get('parsing_errors'):
            print(f"\n⚠️  Warning: {len(result['parsing_errors'])} parsing errors occurred")
            for error in result['parsing_errors'][:3]:
                print(f"   • {error}")
