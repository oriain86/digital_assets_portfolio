# src/core/value_objects/percentage.py

from dataclasses import dataclass
from decimal import Decimal
from typing import Union

from src.core.value_objects.money import Money


@dataclass(frozen=True)
class Percentage:
    """Value object representing a percentage."""

    value: Decimal  # Stored as decimal (0.1 = 10%)

    def __post_init__(self):
        """Validate percentage value."""
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, 'value', Decimal(str(self.value)))

    @classmethod
    def from_percent(cls, percent: Union[int, float, Decimal]) -> 'Percentage':
        """Create from percentage value (10 = 10%)."""
        return cls(Decimal(str(percent)) / 100)

    @classmethod
    def from_decimal(cls, decimal: Union[float, Decimal]) -> 'Percentage':
        """Create from decimal value (0.1 = 10%)."""
        return cls(Decimal(str(decimal)))

    def to_percent(self) -> Decimal:
        """Convert to percentage value (0.1 -> 10)."""
        return self.value * 100

    def apply_to(self, amount: Union[Decimal, Money]) -> Union[Decimal, Money]:
        """Apply percentage to an amount."""
        if isinstance(amount, Money):
            return amount * self.value
        return Decimal(str(amount)) * self.value

    def __add__(self, other: 'Percentage') -> 'Percentage':
        """Add percentages."""
        if not isinstance(other, Percentage):
            raise TypeError(f"Cannot add Percentage and {type(other)}")
        return Percentage(self.value + other.value)

    def __sub__(self, other: 'Percentage') -> 'Percentage':
        """Subtract percentages."""
        if not isinstance(other, Percentage):
            raise TypeError(f"Cannot subtract {type(other)} from Percentage")
        return Percentage(self.value - other.value)

    def __mul__(self, other: Union[int, float, Decimal]) -> 'Percentage':
        """Multiply percentage by scalar."""
        return Percentage(self.value * Decimal(str(other)))

    def __str__(self) -> str:
        """String representation."""
        return f"{self.to_percent():.2f}%"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Percentage({self.value})"
