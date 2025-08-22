
from typing import Dict, Any
from src.application.services.portfolio_service import PortfolioService


class PriceUpdateUseCase:
    """Use case for updating portfolio prices."""

    TRACKED_ASSETS = [
        'BTC', 'ETH', 'BNB', 'SOL', 'MATIC', 'AVAX', 'NEAR', 'FTM',
        'ONE', 'SAND', 'HNT', 'AXS', 'EGLD', 'FET', 'SUI', 'VIRTUAL',
        'LUNA', 'USDT', 'USDC', 'UST'
    ]

    def __init__(self, portfolio_service: PortfolioService):
        self.portfolio_service = portfolio_service

    def execute(self) -> Dict[str, Any]:
        """Update portfolio prices."""
        print("\n💹 Updating current prices...")

        try:
            result = self.portfolio_service.update_portfolio()

            if result['success']:
                print(f"✅ Prices updated successfully!")
                print(f"   Current portfolio value: ${result['total_value']:,.2f}")
            else:
                print(f"⚠️  Warning: Price update failed: {result.get('error')}")
                print("   Using cached prices where available")

            return result

        except Exception as e:
            print(f"⚠️  Warning: Price update failed: {str(e)}")
            print("   Using cached prices where available")
            return {
                'success': False,
                'error': str(e)
            }
