# src/core/value_objects/time_period.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple


@dataclass(frozen=True)
class TimePeriod:
    """Value object representing a time period."""

    start: datetime
    end: datetime

    def __post_init__(self):
        """Validate time period."""
        if self.start > self.end:
            raise ValueError(f"Start date {self.start} cannot be after end date {self.end}")

    @classmethod
    def from_days(cls, days: int, end_date: Optional[datetime] = None) -> 'TimePeriod':
        """Create period from number of days."""
        if end_date is None:
            end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return cls(start_date, end_date)

    @classmethod
    def year_to_date(cls) -> 'TimePeriod':
        """Create year-to-date period."""
        now = datetime.now()
        start = datetime(now.year, 1, 1)
        return cls(start, now)

    @classmethod
    def last_month(cls) -> 'TimePeriod':
        """Create last month period."""
        now = datetime.now()
        if now.month == 1:
            start = datetime(now.year - 1, 12, 1)
            end = datetime(now.year, 1, 1) - timedelta(seconds=1)
        else:
            start = datetime(now.year, now.month - 1, 1)
            end = datetime(now.year, now.month, 1) - timedelta(seconds=1)
        return cls(start, end)

    @classmethod
    def last_year(cls) -> 'TimePeriod':
        """Create last year period."""
        now = datetime.now()
        start = datetime(now.year - 1, 1, 1)
        end = datetime(now.year, 1, 1) - timedelta(seconds=1)
        return cls(start, end)

    @property
    def duration(self) -> timedelta:
        """Get duration of period."""
        return self.end - self.start

    @property
    def days(self) -> int:
        """Get number of days in period."""
        return self.duration.days

    def contains(self, date: datetime) -> bool:
        """Check if date is within period."""
        return self.start <= date <= self.end

    def overlaps(self, other: 'TimePeriod') -> bool:
        """Check if periods overlap."""
        return self.start <= other.end and other.start <= self.end

    def intersection(self, other: 'TimePeriod') -> Optional['TimePeriod']:
        """Get intersection of two periods."""
        if not self.overlaps(other):
            return None
        return TimePeriod(
            max(self.start, other.start),
            min(self.end, other.end)
        )

    def split_by_month(self) -> list['TimePeriod']:
        """Split period into monthly periods."""
        periods = []
        current = self.start.replace(day=1)

        while current <= self.end:
            # Calculate month end
            if current.month == 12:
                month_end = datetime(current.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                month_end = datetime(current.year, current.month + 1, 1) - timedelta(seconds=1)

            # Adjust for period boundaries
            period_start = max(current, self.start)
            period_end = min(month_end, self.end)

            if period_start <= period_end:
                periods.append(TimePeriod(period_start, period_end))

            # Move to next month
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)

        return periods

    def __str__(self) -> str:
        """String representation."""
        return f"{self.start.strftime('%Y-%m-%d')} to {self.end.strftime('%Y-%m-%d')}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"TimePeriod({self.start.isoformat()}, {self.end.isoformat()})"
