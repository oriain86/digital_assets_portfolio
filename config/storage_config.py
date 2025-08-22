# config/storage_config.py

from src.core.entities.transaction import Transaction


class StorageConfig:
    """Configuration for identifying cold storage transfers."""

    # Known cold storage identifiers (customize based on your setup)
    COLD_STORAGE_IDENTIFIERS = [
        'ledger',
        'trezor',
        'cold',
        'hardware',
        'vault',
        'ledger live',  # Add this since you mentioned using Ledger Live
        'nano'  # For Ledger Nano devices
    ]

    # Known hot wallet/exchange identifiers
    HOT_WALLET_IDENTIFIERS = [
        'binance',
        'coinbase',
        'kraken',
        'kucoin',
        'metamask',
        'trust wallet'
    ]

    @classmethod
    def is_cold_storage_transfer(cls, tx: Transaction) -> bool:
        """Check if transaction is likely a cold storage transfer."""
        if not tx.exchange:
            return False

        exchange_lower = tx.exchange.lower()
        return any(identifier in exchange_lower for identifier in cls.COLD_STORAGE_IDENTIFIERS)

    @classmethod
    def is_self_custody_transfer(cls, tx: Transaction, notes: str = None) -> bool:
        """
        Check if this is a transfer between user's own wallets.
        Can check exchange field or notes for hints.
        """
        # Check exchange field
        if cls.is_cold_storage_transfer(tx):
            return True

        # Check notes if provided
        if notes:
            notes_lower = notes.lower()
            transfer_keywords = ['my wallet', 'own wallet', 'self transfer', 'cold storage', 'ledger', 'hardware']
            if any(keyword in notes_lower for keyword in transfer_keywords):
                return True

        # Check transaction notes field
        if tx.notes:
            return cls.is_self_custody_transfer(tx, tx.notes)

        return False
