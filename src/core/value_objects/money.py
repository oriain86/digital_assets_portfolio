# src/core/value_objects/money.py

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional


@dataclass(frozen=True)
class Money:
    """
    Value object representing monetary amounts.
    Ensures precise decimal arithmetic for financial calculations.
    """

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self):
        """Validate and normalize money values."""
        # Ensure amount is Decimal
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))

        # Normalize currency
        object.__setattr__(self, 'currency', self.currency.upper())

    def __add__(self, other: 'Money') -> 'Money':
        """Add two money values."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money and {type(other)}")
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        """Subtract two money values."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract {type(other)} from Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, other: Union[int, float, Decimal]) -> 'Money':
        """Multiply money by a scalar."""
        if isinstance(other, (int, float, Decimal)):
            return Money(self.amount * Decimal(str(other)), self.currency)
        raise TypeError(f"Cannot multiply Money by {type(other)}")

    def __truediv__(self, other: Union[int, float, Decimal, 'Money']) -> Union['Money', Decimal]:
        """Divide money by scalar or another money value."""
        if isinstance(other, (int, float, Decimal)):
            return Money(self.amount / Decimal(str(other)), self.currency)
        elif isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(f"Cannot divide different currencies: {self.currency} and {other.currency}")
            return self.amount / other.amount
        raise TypeError(f"Cannot divide Money by {type(other)}")

    def __neg__(self) -> 'Money':
        """Negate money value."""
        return Money(-self.amount, self.currency)

    def __abs__(self) -> 'Money':
        """Absolute value of money."""
        return Money(abs(self.amount), self.currency)

    def __eq__(self, other) -> bool:
        """Compare equality."""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: 'Money') -> bool:
        """Less than comparison."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money with {type(other)}")
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: 'Money') -> bool:
        """Less than or equal comparison."""
        return self < other or self == other

    def __gt__(self, other: 'Money') -> bool:
        """Greater than comparison."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money with {type(other)}")
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount > other.amount

    def __ge__(self, other: 'Money') -> bool:
        """Greater than or equal comparison."""
        return self > other or self == other

    def round(self, decimals: int = 2) -> 'Money':
        """Round to specified decimal places."""
        quantizer = Decimal(f'0.{"0" * decimals}')
        rounded = self.amount.quantize(quantizer, rounding=ROUND_HALF_UP)
        return Money(rounded, self.currency)

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < 0

    def to_float(self) -> float:
        """Convert to float (use with caution)."""
        return float(self.amount)

    def format(self, include_symbol: bool = True, decimals: Optional[int] = None) -> str:
        """Format money for display."""
        if decimals is not None:
            amount = self.round(decimals).amount
        else:
            amount = self.amount

        if include_symbol:
            if self.currency == 'USD':
                return f"${amount:,.2f}"
            else:
                return f"{amount:,.2f} {self.currency}"
        else:
            return f"{amount:,.2f}"

    def __str__(self) -> str:
        """String representation."""
        return self.format()

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Money({self.amount}, '{self.currency}')"
