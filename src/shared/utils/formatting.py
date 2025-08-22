
from decimal import Decimal
from typing import Union, Optional


def format_currency(amount: Union[Decimal, float],
                    symbol: str = "$",
                    decimals: int = 2) -> str:
    """Format amount as currency."""
    if isinstance(amount, Decimal):
        amount = float(amount)

    if decimals == 0:
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{symbol}{amount:,.{decimals}f}"


def format_percentage(value: Union[Decimal, float],
                      decimals: int = 2,
                      show_sign: bool = True) -> str:
    """Format value as percentage."""
    if isinstance(value, Decimal):
        value = float(value)

    if show_sign and value > 0:
        return f"+{value:.{decimals}f}%"
    else:
        return f"{value:.{decimals}f}%"


def format_crypto_amount(amount: Union[Decimal, float],
                         symbol: Optional[str] = None) -> str:
    """Format cryptocurrency amount."""
    if isinstance(amount, Decimal):
        amount = float(amount)

    if amount < 0.00001:
        formatted = f"{amount:.8f}"
    elif amount < 1:
        formatted = f"{amount:.6f}"
    elif amount < 100:
        formatted = f"{amount:.4f}"
    else:
        formatted = f"{amount:,.2f}"

    if symbol:
        return f"{formatted} {symbol}"
    return formatted
