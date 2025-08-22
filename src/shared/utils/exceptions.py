# src/shared/utils/exceptions.py

class PortfolioException(Exception):
    """Base exception for portfolio-related errors."""
    pass


class ValidationError(PortfolioException):
    """Raised when validation fails."""
    pass


class InsufficientBalanceError(PortfolioException):
    """Raised when trying to sell more than available balance."""
    def __init__(self, asset: str, requested: float, available: float):
        self.asset = asset
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient {asset} balance: requested {requested}, available {available}"
        )


class TransactionError(PortfolioException):
    """Base class for transaction-related errors."""
    pass


class InvalidTransactionError(TransactionError):
    """Raised when a transaction is invalid."""
    pass


class DuplicateTransactionError(TransactionError):
    """Raised when attempting to add a duplicate transaction."""
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        super().__init__(f"Transaction {transaction_id} already exists")


class PriceNotFoundError(PortfolioException):
    """Raised when price data is not available."""
    def __init__(self, asset: str, date=None):
        self.asset = asset
        self.date = date
        if date:
            super().__init__(f"Price not found for {asset} on {date}")
        else:
            super().__init__(f"Price not found for {asset}")


class DataSourceError(PortfolioException):
    """Raised when there's an error with external data sources."""
    pass


class ConfigurationError(PortfolioException):
    """Raised when there's a configuration issue."""
    pass


class CalculationError(PortfolioException):
    """Raised when a calculation fails."""
    pass


class CostBasisError(CalculationError):
    """Raised when cost basis calculation fails."""
    pass


class MetricsError(CalculationError):
    """Raised when metrics calculation fails."""
    pass
