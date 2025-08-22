
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Union, Tuple
import numpy as np


def safe_divide(numerator: Union[Decimal, float],
                denominator: Union[Decimal, float]) -> Union[Decimal, float]:
    """Safely divide two numbers, returning 0 if denominator is 0."""
    if denominator == 0:
        return Decimal('0') if isinstance(numerator, Decimal) else 0.0
    return numerator / denominator


def calculate_compound_return(returns: List[float]) -> float:
    """Calculate compound return from a list of period returns."""
    compound_return = 1.0
    for r in returns:
        compound_return *= (1 + r)
    return compound_return - 1


def calculate_max_drawdown(values: List[float]) -> Tuple[float, int]:
    """Calculate maximum drawdown and duration."""
    if not values or len(values) < 2:
        return 0.0, 0

    peak = values[0]
    max_dd = 0.0
    max_dd_duration = 0
    current_dd_start = 0

    for i, value in enumerate(values):
        if value > peak:
            peak = value
            current_dd_start = i

        dd = (value - peak) / peak if peak > 0 else 0
        if dd < max_dd:
            max_dd = dd
            max_dd_duration = i - current_dd_start

    return max_dd, max_dd_duration


def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """Round decimal to specified places."""
    quantizer = Decimal(f'0.{"0" * places}')
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)
