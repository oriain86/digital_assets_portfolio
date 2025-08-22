# config/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings."""

    # Base paths
    BASE_DIR = Path(__file__).parent.parent  # Goes up from config/ to project root
    DATA_DIR = BASE_DIR / "data"
    LOG_DIR = BASE_DIR / "logs"

    # Data paths
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    CACHE_DIR = DATA_DIR / "cache"

    # Default files - Updated to match your actual file
    DEFAULT_CSV_FILE = "portfolio_transactions.csv"  # Your actual filename
    DEFAULT_PORTFOLIO_CACHE = "portfolio_state.pkl"
    DEFAULT_PRICE_CACHE = "price_cache.json"

    # API Configuration
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

    # Portfolio Configuration
    DEFAULT_PORTFOLIO_NAME = os.getenv("PORTFOLIO_NAME", "My Crypto Portfolio")
    DEFAULT_COST_BASIS_METHOD = os.getenv("COST_BASIS_METHOD", "FIFO")
    DEFAULT_BASE_CURRENCY = os.getenv("BASE_CURRENCY", "USD")
    DEFAULT_RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", "0.02"))

    # Dashboard Configuration
    DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8050"))
    DASHBOARD_DEBUG = os.getenv("DASHBOARD_DEBUG", "False").lower() == "true"

    # Cache Configuration
    PRICE_CACHE_DURATION_MINUTES = int(os.getenv("PRICE_CACHE_DURATION", "5"))
    METRICS_CACHE_DURATION_MINUTES = int(os.getenv("METRICS_CACHE_DURATION", "60"))

    # Performance Configuration
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "True").lower() == "true"

    @classmethod
    def get_csv_path(cls) -> Path:
        """Get path to CSV file - Updated to check both locations."""
        # First check for the file without "raw" subdirectory
        direct_path = cls.DATA_DIR / cls.DEFAULT_CSV_FILE
        if direct_path.exists():
            return direct_path

        # Then check in raw subdirectory
        raw_path = cls.RAW_DATA_DIR / cls.DEFAULT_CSV_FILE
        if raw_path.exists():
            return raw_path

        # Default to raw path if neither exists
        return raw_path

    @classmethod
    def get_portfolio_cache_path(cls) -> Path:
        """Get path to portfolio cache file."""
        return cls.CACHE_DIR / cls.DEFAULT_PORTFOLIO_CACHE

    @classmethod
    def get_price_cache_path(cls) -> Path:
        """Get path to price cache file."""
        return cls.CACHE_DIR / cls.DEFAULT_PRICE_CACHE

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        directories = [
            cls.DATA_DIR,
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.CACHE_DIR,
            cls.LOG_DIR
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Create settings instance
settings = Settings()
