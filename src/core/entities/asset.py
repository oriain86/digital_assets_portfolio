# src/core/entities/asset.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
from decimal import Decimal


@dataclass
class Asset:
    """
    Represents a cryptocurrency or fiat asset.

    This entity encapsulates asset-specific information and behavior.
    """

    symbol: str
    name: Optional[str] = None
    asset_type: str = "crypto"  # crypto, fiat, stablecoin
    decimals: int = 8
    coingecko_id: Optional[str] = None

    # Market data
    current_price: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    price_change_24h: Optional[float] = None

    def __post_init__(self):
        """Normalize asset data."""
        self.symbol = self.symbol.upper().strip()

        # Set default names if not provided
        if not self.name:
            self.name = self.symbol

        # Identify asset type
        if self.symbol in ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD']:
            self.asset_type = 'fiat'
            self.decimals = 2
        elif self.symbol in ['USDC', 'USDT', 'DAI', 'BUSD', 'UST', 'TUSD']:
            self.asset_type = 'stablecoin'
            self.decimals = 6

    def is_stablecoin(self) -> bool:
        """Check if asset is a stablecoin."""
        return self.asset_type == 'stablecoin'

    def is_fiat(self) -> bool:
        """Check if asset is fiat currency."""
        return self.asset_type == 'fiat'

    def is_crypto(self) -> bool:
        """Check if asset is a cryptocurrency."""
        return self.asset_type == 'crypto' and not self.is_stablecoin()

    def format_amount(self, amount: Decimal) -> str:
        """Format amount with appropriate decimal places."""
        if self.is_fiat() or self.is_stablecoin():
            return f"{amount:,.2f}"
        else:
            # For crypto, show more decimals for small amounts
            if amount < 1:
                return f"{amount:.8f}".rstrip('0').rstrip('.')
            elif amount < 100:
                return f"{amount:.4f}".rstrip('0').rstrip('.')
            else:
                return f"{amount:,.2f}"

    def format_price(self, price: Decimal) -> str:
        """Format price in USD."""
        if price < 0.01:
            return f"${price:.6f}"
        elif price < 1:
            return f"${price:.4f}"
        else:
            return f"${price:,.2f}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'type': self.asset_type,
            'decimals': self.decimals,
            'current_price': float(self.current_price) if self.current_price else None,
            'market_cap': float(self.market_cap) if self.market_cap else None,
            'volume_24h': float(self.volume_24h) if self.volume_24h else None,
            'price_change_24h': self.price_change_24h
        }


# Common assets registry
COMMON_ASSETS = {
    'BTC': Asset('BTC', 'Bitcoin', coingecko_id='bitcoin'),
    'ETH': Asset('ETH', 'Ethereum', coingecko_id='ethereum'),
    'BNB': Asset('BNB', 'Binance Coin', coingecko_id='binancecoin'),
    'SOL': Asset('SOL', 'Solana', coingecko_id='solana'),
    'AVAX': Asset('AVAX', 'Avalanche', coingecko_id='avalanche-2'),
    'MATIC': Asset('MATIC', 'Polygon', coingecko_id='matic-network'),
    'NEAR': Asset('NEAR', 'NEAR Protocol', coingecko_id='near'),
    'USD': Asset('USD', 'US Dollar', asset_type='fiat'),
    'USDC': Asset('USDC', 'USD Coin', asset_type='stablecoin'),
    'USDT': Asset('USDT', 'Tether', asset_type='stablecoin'),
}
