# src/shared/utils/constants.py

from decimal import Decimal
from enum import Enum


# Decimal constants
ZERO = Decimal('0')
ONE = Decimal('1')
HUNDRED = Decimal('100')

# Trading constants
MIN_TRADE_AMOUNT = Decimal('0.00000001')  # Satoshi
MAX_DECIMAL_PLACES = 8

# Fee constants
DEFAULT_TRADING_FEE_PERCENT = Decimal('0.001')  # 0.1%
DEFAULT_NETWORK_FEE = Decimal('0')

# Time constants
SECONDS_PER_DAY = 86400
DAYS_PER_YEAR = 365
CRYPTO_TRADING_DAYS_PER_YEAR = 365  # Crypto trades 24/7
TRADITIONAL_TRADING_DAYS_PER_YEAR = 252

# Risk constants
DEFAULT_RISK_FREE_RATE = 0.02  # 2% annual
DEFAULT_CONFIDENCE_LEVEL = 0.95  # For VaR calculations

# Display constants
DEFAULT_CURRENCY_SYMBOL = '$'
DEFAULT_DECIMAL_DISPLAY = 2
CRYPTO_DECIMAL_DISPLAY = 8

# Cache constants
PRICE_CACHE_DURATION_MINUTES = 5
METRICS_CACHE_DURATION_MINUTES = 60

# Batch processing
DEFAULT_BATCH_SIZE = 1000
MAX_TRANSACTIONS_PER_BATCH = 5000

# API rate limits
COINGECKO_RATE_LIMIT_PER_MINUTE = 50
BINANCE_RATE_LIMIT_PER_MINUTE = 1200

# File paths
DEFAULT_DATA_PATH = "data/"
DEFAULT_CACHE_PATH = "data/cache/"
DEFAULT_LOG_PATH = "logs/"

# Supported exchanges
SUPPORTED_EXCHANGES = [
    'Coinbase',
    'Coinbase Pro',
    'Binance',
    'Binance US',
    'Kraken',
    'Gemini',
    'FTX',
    'KuCoin',
    'Crypto.com',
    'Bitstamp'
]

# Asset classifications
STABLECOINS = ['USDC', 'USDT', 'DAI', 'BUSD', 'UST', 'TUSD', 'USDP', 'FRAX']
FIAT_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF']
WRAPPED_TOKENS = ['WBTC', 'WETH', 'WBNB', 'WAVAX']

# Tax categories
class TaxCategory(Enum):
    SHORT_TERM = "short_term"  # Held < 1 year
    LONG_TERM = "long_term"    # Held >= 1 year

# Cost basis methods
class CostBasisMethod(Enum):
    FIFO = "FIFO"  # First In First Out
    LIFO = "LIFO"  # Last In First Out
    HIFO = "HIFO"  # Highest In First Out
    SPECIFIC_ID = "SPECIFIC_ID"  # Specific Identification

# Performance periods
class PerformancePeriod(Enum):
    DAILY = "1D"
    WEEKLY = "1W"
    MONTHLY = "1M"
    QUARTERLY = "3M"
    YEARLY = "1Y"
    ALL_TIME = "ALL"

# Chart themes
CHART_THEME = {
    'background_color': '#111827',
    'grid_color': '#374151',
    'text_color': '#F3F4F6',
    'positive_color': '#10B981',
    'negative_color': '#EF4444',
    'primary_color': '#3B82F6',
    'secondary_color': '#8B5CF6',
    'warning_color': '#F59E0B'
}

# Metrics thresholds
GOOD_SHARPE_RATIO = 1.0
EXCELLENT_SHARPE_RATIO = 2.0
WARNING_MAX_DRAWDOWN = -0.20  # -20%
DANGER_MAX_DRAWDOWN = -0.40   # -40%

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Error messages
ERROR_MESSAGES = {
    'INVALID_AMOUNT': "Invalid amount: must be positive",
    'INVALID_PRICE': "Invalid price: must be positive",
    'INVALID_DATE': "Invalid date format",
    'INSUFFICIENT_BALANCE': "Insufficient balance for transaction",
    'DUPLICATE_TRANSACTION': "Transaction already exists",
    'INVALID_TRANSACTION_TYPE': "Invalid transaction type",
    'PRICE_NOT_FOUND': "Price data not available",
    'CALCULATION_ERROR': "Error in calculation",
    'API_ERROR': "External API error",
    'FILE_NOT_FOUND': "File not found",
    'INVALID_CSV_FORMAT': "Invalid CSV format"
}
