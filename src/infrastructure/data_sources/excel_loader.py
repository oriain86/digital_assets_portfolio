
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging

from src.core.entities.transaction import Transaction
from src.infrastructure.data_sources.unified_csv_loader import UnifiedCSVLoader

logger = logging.getLogger(__name__)


class ExcelLoader:
    """Loader for Excel transaction files."""

    def __init__(self):
        self.csv_loader = UnifiedCSVLoader()

    def load_transactions(self, file_path: str, sheet_name: Optional[str] = None) -> List[Transaction]:
        """Load transactions from Excel file."""
        try:
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                # Read first sheet by default
                df = pd.read_excel(file_path)

            # Convert to CSV format in memory
            csv_buffer = df.to_csv(index=False)

            # Use CSV loader logic
            # This is a simplified approach - you might want to handle Excel-specific formats
            temp_csv_path = Path(file_path).with_suffix('.csv')
            temp_csv_path.write_text(csv_buffer)

            try:
                transactions = self.csv_loader.load_transactions(str(temp_csv_path))
                return transactions
            finally:
                # Clean up temp file
                if temp_csv_path.exists():
                    temp_csv_path.unlink()

        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            raise