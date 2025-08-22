# src/application/startup.py

import sys
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from config.settings import settings
from config.logging import setup_logging
from src.application.services.portfolio_service import PortfolioService
from src.core.entities.portfolio import Portfolio


@dataclass
class StartupConfig:
    """Configuration for application startup."""
    data_dir: str
    cache_dir: str
    cost_basis_method: str
    dashboard_port: int
    dashboard_host: str
    dashboard_debug: bool


class ApplicationStartup:
    """Handles application initialization and startup logic."""

    @staticmethod
    def print_banner():
        """Print application banner."""
        banner = """
        ╔═══════════════════════════════════════════════════════════╗
        ║       🚀 Crypto Portfolio Performance Tracker 🚀          ║
        ║                                                           ║
        ║  Professional-grade analytics with cost basis tracking    ║
        ╚═══════════════════════════════════════════════════════════╝
        """
        print(banner)

    @staticmethod
    def setup_environment() -> StartupConfig:
        """Setup application environment and return configuration."""
        # Setup logging
        try:
            setup_logging(
                log_level=settings.LOG_LEVEL,
                log_dir=str(settings.LOG_DIR),
                log_to_console=settings.LOG_TO_CONSOLE,
                log_to_file=settings.LOG_TO_FILE
            )
        except Exception as e:
            print(f"⚠️  Warning: Could not setup logging: {e}")

        # Ensure directories exist
        try:
            settings.ensure_directories()
        except Exception as e:
            print(f"⚠️  Warning: Could not create directories: {e}")
            # Fallback directory creation
            for dir_path in ['data', 'data/raw', 'data/processed', 'data/cache', 'logs']:
                Path(dir_path).mkdir(parents=True, exist_ok=True)

        return StartupConfig(
            data_dir=str(settings.DATA_DIR),
            cache_dir=str(settings.CACHE_DIR),
            cost_basis_method=settings.DEFAULT_COST_BASIS_METHOD,
            dashboard_port=settings.DASHBOARD_PORT,
            dashboard_host=settings.DASHBOARD_HOST,
            dashboard_debug=settings.DASHBOARD_DEBUG
        )

    @staticmethod
    def initialize_portfolio_service(config: StartupConfig) -> Optional[PortfolioService]:
        """Initialize portfolio service."""
        try:
            return PortfolioService(
                data_path=config.data_dir,
                cache_path=config.cache_dir,
                cost_basis_method=config.cost_basis_method
            )
        except Exception as e:
            print(f"❌ Error initializing portfolio service: {e}")
            return None

    @staticmethod
    def check_or_init_portfolio(
            portfolio_service: PortfolioService
    ) -> Tuple[bool, Optional[Portfolio]]:
        """Check for existing portfolio or initialize new one."""
        try:
            if portfolio_service.load_portfolio():
                return True, portfolio_service.get_portfolio()
        except Exception as e:
            print(f"⚠️  Could not load existing portfolio: {e}")

        # No existing portfolio - check for CSV
        print("\n🔍 No existing portfolio found.")
        csv_path = settings.get_csv_path()

        if not csv_path.exists():
            ApplicationStartup._print_csv_instructions(csv_path)
            return False, None

        # Initialize from CSV
        from src.application.use_cases.portfolio_initialization import PortfolioInitializationUseCase
        init_use_case = PortfolioInitializationUseCase(portfolio_service)

        result = init_use_case.execute(str(csv_path))
        if result['success']:
            return True, portfolio_service.get_portfolio()
        else:
            print(f"\n❌ Failed to initialize portfolio: {result.get('error')}")
            return False, None

    @staticmethod
    def _print_csv_instructions(csv_path: Path):
        """Print instructions for CSV setup."""
        print(f"\n❌ CSV file not found at: {csv_path}")
        print("\n📝 To get started:")
        print(f"   1. Place your transaction CSV file at: {csv_path}")
        print("   2. Run this program again")
        print("\n📋 Required CSV columns:")
        print("   • timestamp")
        print("   • type (Buy, Sell, Deposit, Withdrawal, etc.)")
        print("   • asset (BTC, ETH, etc.)")
        print("   • amount")
        print("   • price_usd (optional)")
        print("   • total_usd (optional)")
        print("   • fee_usd (optional)")
        print("   • exchange (optional)")
        print("   • transaction_id (optional)")
        print("   • notes (optional)")
