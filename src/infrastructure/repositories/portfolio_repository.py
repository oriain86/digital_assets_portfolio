# src/infrastructure/repositories/portfolio_repository.py

import pickle
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from decimal import Decimal

from src.core.interfaces.repository import PortfolioRepository as IPortfolioRepository
from src.core.entities.portfolio import Portfolio, PortfolioSnapshot
from src.shared.utils.exceptions import DataSourceError

logger = logging.getLogger(__name__)


class FilePortfolioRepository(IPortfolioRepository):
    """File-based implementation of portfolio repository."""

    def __init__(self, base_path: str = "data/portfolios"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, portfolio: Portfolio) -> None:
        """Save portfolio state to file."""
        try:
            portfolio_id = portfolio.name.lower().replace(" ", "_")
            file_path = self.base_path / f"{portfolio_id}.pkl"

            with open(file_path, 'wb') as f:
                pickle.dump(portfolio, f)

            logger.info(f"Saved portfolio to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save portfolio: {e}")
            raise DataSourceError(f"Failed to save portfolio: {e}")

    def load(self, portfolio_id: str) -> Optional[Portfolio]:
        """Load portfolio from file."""
        try:
            file_path = self.base_path / f"{portfolio_id}.pkl"

            if not file_path.exists():
                return None

            with open(file_path, 'rb') as f:
                portfolio = pickle.load(f)

            logger.info(f"Loaded portfolio from {file_path}")
            return portfolio

        except Exception as e:
            logger.error(f"Failed to load portfolio: {e}")
            raise DataSourceError(f"Failed to load portfolio: {e}")

    def save_snapshot(self, portfolio_id: str, snapshot: PortfolioSnapshot) -> None:
        """Save portfolio snapshot to JSON file."""
        try:
            snapshot_dir = self.base_path / portfolio_id / "snapshots"
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            # Create filename with timestamp
            timestamp_str = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
            file_path = snapshot_dir / f"snapshot_{timestamp_str}.json"

            # Convert snapshot to JSON-serializable format
            snapshot_data = {
                'timestamp': snapshot.timestamp.isoformat(),
                'total_value': float(snapshot.total_value),
                'positions': snapshot.positions,
                'realized_pnl': float(snapshot.realized_pnl),
                'unrealized_pnl': float(snapshot.unrealized_pnl),
                'cash_balance': float(snapshot.cash_balance)
            }

            with open(file_path, 'w') as f:
                json.dump(snapshot_data, f, indent=2)

            logger.debug(f"Saved snapshot to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            raise DataSourceError(f"Failed to save snapshot: {e}")

    def get_snapshots(self, portfolio_id: str,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[PortfolioSnapshot]:
        """Load portfolio snapshots from files."""
        try:
            snapshot_dir = self.base_path / portfolio_id / "snapshots"

            if not snapshot_dir.exists():
                return []

            snapshots = []

            for file_path in snapshot_dir.glob("snapshot_*.json"):
                with open(file_path, 'r') as f:
                    data = json.load(f)

                timestamp = datetime.fromisoformat(data['timestamp'])

                # Filter by date range if provided
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue

                snapshot = PortfolioSnapshot(
                    timestamp=timestamp,
                    total_value=Decimal(str(data['total_value'])),
                    positions=data['positions'],
                    realized_pnl=Decimal(str(data['realized_pnl'])),
                    unrealized_pnl=Decimal(str(data['unrealized_pnl'])),
                    cash_balance=Decimal(str(data['cash_balance']))
                )
                snapshots.append(snapshot)

            # Sort by timestamp
            snapshots.sort(key=lambda x: x.timestamp)

            logger.info(f"Loaded {len(snapshots)} snapshots for {portfolio_id}")
            return snapshots

        except Exception as e:
            logger.error(f"Failed to load snapshots: {e}")
            raise DataSourceError(f"Failed to load snapshots: {e}")

    def delete(self, portfolio_id: str) -> None:
        """Delete portfolio and all associated data."""
        try:
            # Delete main portfolio file
            portfolio_file = self.base_path / f"{portfolio_id}.pkl"
            if portfolio_file.exists():
                portfolio_file.unlink()

            # Delete snapshots directory
            snapshot_dir = self.base_path / portfolio_id
            if snapshot_dir.exists():
                import shutil
                shutil.rmtree(snapshot_dir)

            logger.info(f"Deleted portfolio {portfolio_id}")

        except Exception as e:
            logger.error(f"Failed to delete portfolio: {e}")
            raise DataSourceError(f"Failed to delete portfolio: {e}")
