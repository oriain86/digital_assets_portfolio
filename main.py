# main.py

import logging
import sys
import webbrowser
from threading import Timer

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

from src.application.services.portfolio_service import PortfolioService
from src.application.use_cases.portfolio_display import PortfolioDisplayUseCase
from src.application.use_cases.price_update import PriceUpdateUseCase
from src.presentation.dashboard.app import DashboardApp


def display_banner():
    """Display the application banner."""
    banner = """
        ╔═══════════════════════════════════════════════════════════╗
        ║       🚀 Crypto Portfolio Performance Tracker 🚀          ║
        ║                                                           ║
        ║  Professional-grade analytics with cost basis tracking    ║
        ╚═══════════════════════════════════════════════════════════╝
        """
    print(banner)


def open_browser():
    """Open the dashboard in the default browser."""
    webbrowser.open('http://localhost:8050')


def main():
    """Main entry point for the Crypto Portfolio Tracker."""
    display_banner()

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Crypto Portfolio Tracker - Starting")
    logger.info("=" * 60)

    try:
        # Initialize portfolio service
        portfolio_service = PortfolioService()

        # Check if portfolio exists
        if not portfolio_service.load_portfolio():
            logger.warning("No existing portfolio found. Please initialize a portfolio first.")
            print("\n⚠️  No portfolio found. Please run the initialization script first.")
            return

        # Show portfolio summary
        display_use_case = PortfolioDisplayUseCase(portfolio_service)
        display_use_case.show_summary()

        # Update prices
        print("\n💹 Updating current prices...")
        try:
            # Use the portfolio service's update method
            result = portfolio_service.update_portfolio()
            if result.get('success'):
                print("✅ Prices updated successfully!")
            else:
                print(f"⚠️  Could not update prices: {result.get('error', 'Unknown error')}")
                print("   Continuing with cached prices...")
        except Exception as e:
            print(f"⚠️  Could not update prices: {e}")
            print("   Continuing with cached prices...")

        # Start dashboard
        print("\n🌐 Starting web dashboard...")
        print("   URL: http://localhost:8050")
        print("   Press Ctrl+C to stop")

        # Auto-open browser after 2 seconds
        Timer(2.0, open_browser).start()

        dashboard = DashboardApp(portfolio_service)
        dashboard.run(debug=False, host='0.0.0.0', port=8050)

    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
