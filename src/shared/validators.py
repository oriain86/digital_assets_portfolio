# src/shared/validators.py

from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Optional, Union
import re

from src.shared.utils.exceptions import ValidationError
from src.shared.constants import MIN_TRADE_AMOUNT, MAX_DECIMAL_PLACES


def validate_positive_decimal(value: Any, field_name: str) -> Decimal:
    """Validate and convert to positive decimal."""
    try:
        decimal_value = Decimal(str(value))
        if decimal_value <= 0:
            raise ValidationError(f"{field_name} must be positive, got {value}")
        return decimal_value
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid decimal value for {field_name}: {value}")


def validate_non_negative_decimal(value: Any, field_name: str) -> Decimal:
    """Validate and convert to non-negative decimal."""
    try:
        decimal_value = Decimal(str(value))
        if decimal_value < 0:
            raise ValidationError(f"{field_name} cannot be negative, got {value}")
        return decimal_value
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid decimal value for {field_name}: {value}")


def validate_decimal(value: Any, field_name: str) -> Decimal:
    """Validate and convert to decimal (can be negative)."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid decimal value for {field_name}: {value}")


def validate_amount(amount: Any, min_amount: Decimal = MIN_TRADE_AMOUNT) -> Decimal:
    """Validate transaction amount."""
    decimal_amount = validate_positive_decimal(amount, "Amount")

    if decimal_amount < min_amount:
        raise ValidationError(f"Amount {decimal_amount} is below minimum {min_amount}")

    # Check decimal places
    decimal_places = abs(decimal_amount.as_tuple().exponent)
    if decimal_places > MAX_DECIMAL_PLACES:
        raise ValidationError(f"Amount has too many decimal places: {decimal_places} > {MAX_DECIMAL_PLACES}")

    return decimal_amount


def validate_price(price: Any) -> Decimal:
    """Validate price value."""
    return validate_positive_decimal(price, "Price")


def validate_asset_symbol(symbol: Any) -> str:
    """Validate and normalize asset symbol."""
    if not symbol:
        raise ValidationError("Asset symbol cannot be empty")

    symbol_str = str(symbol).strip().upper()

    # Check for valid characters (letters, numbers, hyphen)
    if not re.match(r'^[A-Z0-9\-]+$', symbol_str):
        raise ValidationError(f"Invalid asset symbol: {symbol}")

    # Check length
    if len(symbol_str) > 10:
        raise ValidationError(f"Asset symbol too long: {symbol_str}")

    return symbol_str


def validate_exchange_name(exchange: Any) -> str:
    """Validate and normalize exchange name."""
    if not exchange:
        return ""  # Exchange is optional

    exchange_str = str(exchange).strip()

    # Basic validation - no special characters except space and dot
    if not re.match(r'^[A-Za-z0-9\s\.]+$', exchange_str):
        raise ValidationError(f"Invalid exchange name: {exchange}")

    return exchange_str


def validate_transaction_id(tx_id: Any) -> str:
    """Validate transaction ID."""
    if not tx_id:
        return ""  # Transaction ID can be auto-generated

    tx_id_str = str(tx_id).strip()

    # Allow alphanumeric, underscore, hyphen
    if not re.match(r'^[A-Za-z0-9_\-]+$', tx_id_str):
        raise ValidationError(f"Invalid transaction ID: {tx_id}")

    return tx_id_str


def validate_datetime(value: Any, field_name: str = "Datetime") -> datetime:
    """Validate datetime value."""
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        # Try common datetime formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d.%m.%Y %H:%M:%S",
            "%d.%m.%Y %H:%M",
            "%d.%m.%Y",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue

        raise ValidationError(f"Invalid datetime format for {field_name}: {value}")

    raise ValidationError(f"Invalid datetime type for {field_name}: {type(value)}")


def validate_percentage(value: Any, field_name: str = "Percentage") -> Decimal:
    """Validate percentage value (0-100)."""
    decimal_value = validate_decimal(value, field_name)

    if decimal_value < 0 or decimal_value > 100:
        raise ValidationError(f"{field_name} must be between 0 and 100, got {decimal_value}")

    return decimal_value


def validate_email(email: Any) -> str:
    """Validate email address."""
    if not email:
        return ""

    email_str = str(email).strip().lower()

    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email_str):
        raise ValidationError(f"Invalid email address: {email}")

    return email_str


def validate_currency_code(currency: Any) -> str:
    """Validate currency code (ISO 4217)."""
    if not currency:
        raise ValidationError("Currency code cannot be empty")

    currency_str = str(currency).strip().upper()

    # Check for 3-letter code
    if not re.match(r'^[A-Z]{3}$', currency_str):
        raise ValidationError(f"Invalid currency code: {currency} (must be 3 letters)")

    return currency_str


def validate_csv_headers(headers: list, required_headers: list) -> None:
    """Validate CSV headers contain required fields."""
    # Normalize headers
    normalized_headers = [h.strip().lower() for h in headers]
    required_normalized = [h.strip().lower() for h in required_headers]

    missing = []
    for required in required_normalized:
        if required not in normalized_headers:
            missing.append(required)

    if missing:
        raise ValidationError(f"Missing required CSV headers: {', '.join(missing)}")


def validate_file_path(path: Any, must_exist: bool = True) -> str:
    """Validate file path."""
    from pathlib import Path

    try:
        path_obj = Path(str(path))

        if must_exist and not path_obj.exists():
            raise ValidationError(f"File not found: {path}")

        return str(path_obj)
    except Exception as e:
        raise ValidationError(f"Invalid file path: {path} - {str(e)}")


def validate_batch_size(size: Any) -> int:
    """Validate batch size."""
    try:
        size_int = int(size)
        if size_int <= 0:
            raise ValidationError(f"Batch size must be positive, got {size}")
        if size_int > 10000:
            raise ValidationError(f"Batch size too large: {size} (max 10000)")
        return size_int
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid batch size: {size}")


def validate_json_string(json_str: Any) -> dict:
    """Validate JSON string and return parsed object."""
    import json

    try:
        return json.loads(str(json_str))
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON: {str(e)}")


def validate_cost_basis_method(method: Any) -> str:
    """Validate cost basis method."""
    valid_methods = ['FIFO', 'LIFO', 'HIFO', 'SPECIFIC_ID']

    method_str = str(method).strip().upper()

    if method_str not in valid_methods:
        raise ValidationError(
            f"Invalid cost basis method: {method}. "
            f"Must be one of: {', '.join(valid_methods)}"
        )

    return method_str
