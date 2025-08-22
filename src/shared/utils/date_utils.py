
from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_date_range(range_str: str) -> Tuple[datetime, datetime]:
    """Parse date range string (e.g., '1M', '3M', '1Y', 'YTD')."""
    now = datetime.now()

    if range_str == 'YTD':
        start = datetime(now.year, 1, 1)
        return start, now

    # Parse number and unit
    unit = range_str[-1]
    number = int(range_str[:-1])

    if unit == 'D':
        start = now - timedelta(days=number)
    elif unit == 'M':
        start = now - timedelta(days=number * 30)
    elif unit == 'Y':
        start = now - timedelta(days=number * 365)
    else:
        raise ValueError(f"Invalid range string: {range_str}")

    return start, now


def format_duration(seconds: int) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"
