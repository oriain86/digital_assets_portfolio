# src/core/entities/transaction.py

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
import hashlib
import json


class TransactionType(Enum):
    """Enumeration of all possible transaction types in the crypto portfolio."""
    BUY = "Buy"
    SELL = "Sell"
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    SEND = "Send"
    RECEIVE = "Receive"
    CONVERT_FROM = "Convert (from)"
    CONVERT_TO = "Convert (to)"
    REWARD = "Reward / Bonus"
    STAKING = "Staking"
    UNSTAKING = "Unstaking"
    INTEREST = "Interest"
    AIRDROP = "Airdrop"

    @classmethod
    def from_string(cls, value: str) -> 'TransactionType':
        """Convert string to TransactionType, handling various formats."""
        value = value.strip()
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f"Invalid transaction type: {value}")

    def is_acquisition(self) -> bool:
        """Check if this transaction type represents acquiring an asset."""
        return self in [
            TransactionType.BUY,
            TransactionType.RECEIVE,
            TransactionType.CONVERT_TO,
            TransactionType.REWARD,
            TransactionType.INTEREST,
            TransactionType.AIRDROP,
            TransactionType.DEPOSIT
        ]

    def is_disposal(self) -> bool:
        """Check if this transaction type represents disposing of an asset."""
        return self in [
            TransactionType.SELL,
            TransactionType.SEND,
            TransactionType.CONVERT_FROM,
            TransactionType.WITHDRAWAL
        ]

    def affects_cost_basis(self) -> bool:
        """Check if this transaction type affects cost basis calculations."""
        return self not in [TransactionType.DEPOSIT, TransactionType.WITHDRAWAL]


@dataclass
class Transaction:
    """
    Core domain entity representing a single crypto transaction.

    This class encapsulates all the business logic related to a transaction,
    including validation, cost basis calculations, and transaction matching.
    """

    timestamp: datetime
    type: TransactionType
    asset: str
    amount: Decimal
    price_usd: Optional[Decimal] = None
    total_usd: Optional[Decimal] = None
    fee_usd: Optional[Decimal] = None
    exchange: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None

    # Additional fields for advanced tracking
    cost_basis: Optional[Decimal] = field(default=None, init=False)
    realized_gain_loss: Optional[Decimal] = field(default=None, init=False)
    matched_transaction_id: Optional[str] = field(default=None, init=False)

    def __post_init__(self):
        """Validate and normalize transaction data after initialization."""
        self._validate()
        self._normalize()
        self._calculate_derived_fields()

    def _validate(self):
        """Validate transaction data integrity."""
        if self.amount <= 0:
            raise ValueError(f"Transaction amount must be positive: {self.amount}")

        if self.asset.upper() in ['USD', 'USDC', 'USDT', 'DAI', 'BUSD'] and self.type.affects_cost_basis():
            # Stablecoins should have price close to 1
            if self.price_usd and abs(self.price_usd - Decimal('1')) > Decimal('0.1'):
                print(f"Warning: Unusual price for stablecoin {self.asset}: ${self.price_usd}")

        if self.type.is_acquisition() or self.type.is_disposal():
            if not self.price_usd and not self.total_usd:
                raise ValueError(f"Price or total USD required for {self.type.value} transaction")

        if self.price_usd and self.total_usd:
            calculated_total = self.amount * self.price_usd
            if abs(calculated_total - self.total_usd) > Decimal('0.01'):
                # Log warning instead of raising error
                print(f"Warning: Price/Total mismatch for {self.asset}: "
                      f"calculated ${calculated_total:.2f} vs provided ${self.total_usd:.2f}")

    def _normalize(self):
        """Normalize transaction data for consistency."""
        self.asset = self.asset.upper().strip()
        if self.exchange:
            self.exchange = self.exchange.strip()

        # Ensure fee is positive
        if self.fee_usd and self.fee_usd < 0:
            self.fee_usd = abs(self.fee_usd)

    def _calculate_derived_fields(self):
        """Calculate fields that can be derived from other fields."""
        # Calculate total_usd if not provided
        if not self.total_usd and self.price_usd:
            self.total_usd = self.amount * self.price_usd

        # Calculate price_usd if not provided
        elif not self.price_usd and self.total_usd:
            self.price_usd = self.total_usd / self.amount

        # Generate transaction hash if no ID provided
        if not self.transaction_id:
            self.transaction_id = self._generate_transaction_hash()

    def _generate_transaction_hash(self) -> str:
        """Generate a unique hash for the transaction based on its properties."""
        data = {
            'timestamp': self.timestamp.isoformat(),
            'type': self.type.value,
            'asset': self.asset,
            'amount': str(self.amount),
            'exchange': self.exchange or 'unknown',
            'total_usd': str(self.total_usd) if self.total_usd else '0'
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def get_effective_cost(self) -> Decimal:
        """Get the effective cost of the transaction including fees."""
        if self.type.is_acquisition():
            # For buys, add the fee to the cost
            base_cost = self.total_usd or (self.amount * self.price_usd)
            return base_cost + (self.fee_usd or Decimal('0'))
        elif self.type.is_disposal():
            # For sells, subtract the fee from the proceeds
            base_proceeds = self.total_usd or (self.amount * self.price_usd)
            return base_proceeds - (self.fee_usd or Decimal('0'))
        return Decimal('0')

    def get_effective_price(self) -> Decimal:
        """Get the effective price per unit including fees."""
        if self.amount == 0:
            return Decimal('0')
        return self.get_effective_cost() / self.amount

    def is_conversion_pair(self, other: 'Transaction') -> bool:
        """Check if this transaction is part of a conversion pair with another."""
        if not (self.type == TransactionType.CONVERT_FROM and other.type == TransactionType.CONVERT_TO) and \
                not (self.type == TransactionType.CONVERT_TO and other.type == TransactionType.CONVERT_FROM):
            return False

        # Check if timestamps are close (within 1 minute)
        time_diff = abs((self.timestamp - other.timestamp).total_seconds())
        if time_diff > 60:
            return False

        # Check if exchanges match
        if self.exchange != other.exchange:
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'type': self.type.value,
            'asset': self.asset,
            'amount': str(self.amount),
            'price_usd': str(self.price_usd) if self.price_usd else None,
            'total_usd': str(self.total_usd) if self.total_usd else None,
            'fee_usd': str(self.fee_usd) if self.fee_usd else None,
            'exchange': self.exchange,
            'transaction_id': self.transaction_id,
            'notes': self.notes,
            'cost_basis': str(self.cost_basis) if self.cost_basis else None,
            'realized_gain_loss': str(self.realized_gain_loss) if self.realized_gain_loss else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create transaction from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            type=TransactionType.from_string(data['type']),
            asset=data['asset'],
            amount=Decimal(data['amount']),
            price_usd=Decimal(data['price_usd']) if data.get('price_usd') else None,
            total_usd=Decimal(data['total_usd']) if data.get('total_usd') else None,
            fee_usd=Decimal(data['fee_usd']) if data.get('fee_usd') else None,
            exchange=data.get('exchange'),
            transaction_id=data.get('transaction_id'),
            notes=data.get('notes')
        )

    def __str__(self) -> str:
        """String representation of the transaction."""
        return (f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} - "
                f"{self.type.value} {self.amount:.8f} {self.asset} "
                f"@ ${self.price_usd:.2f}" if self.price_usd else "")

    def __hash__(self) -> int:
        """Make transaction hashable for use in sets and dicts."""
        return hash(self.transaction_id)

    def __eq__(self, other) -> bool:
        """Check equality based on transaction ID."""
        if not isinstance(other, Transaction):
            return False
        return self.transaction_id == other.transaction_id
