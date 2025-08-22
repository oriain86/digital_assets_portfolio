# src/infrastructure/data_sources/price_fetcher.py

from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal
import logging
import time
from functools import wraps

from src.infrastructure.data_sources.api_client import APIClient
from src.infrastructure.cache.price_cache import PriceCache

logger = logging.getLogger(__name__)


def rate_limit(calls_per_minute: int = 50):
    """Rate limiting decorator."""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret

        return wrapper

    return decorator


class PriceFetcher:
    """Fetches cryptocurrency prices from multiple sources with rate limiting."""

    def __init__(self, cache_dir: str = "data/cache"):
        self.coingecko_client = APIClient("https://api.coingecko.com/api/v3")
        self.cache = PriceCache(cache_dir)
        self.rate_limit_delay = 1.2  # 50 calls per minute for free tier
        self.last_api_call = 0

        # Complete symbol to CoinGecko ID mapping based on your trades
        self.symbol_map = {
            # Major cryptocurrencies
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network',

            # Stablecoins
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'USD': 'usd',  # Fiat currency

            # DeFi & Gaming tokens
            'UNI': 'uniswap',
            'LINK': 'chainlink',
            'AAVE': 'aave',
            'AXS': 'axie-infinity',
            'SAND': 'the-sandbox',
            'MANA': 'decentraland',
            'ENJ': 'enjincoin',
            'GALA': 'gala',

            # Layer 1 & 2 tokens
            'FTM': 'fantom',
            'ONE': 'harmony',
            'NEAR': 'near',
            'LUNA': 'terra-luna',  # Classic Luna
            'ATOM': 'cosmos',
            'DOT': 'polkadot',
            'ADA': 'cardano',
            'ALGO': 'algorand',
            'EGLD': 'elrond-erd-2',
            'HNT': 'helium',

            # AI & Other tokens
            'FET': 'fetch-ai',
            'VIRTUAL': 'virtual-protocol',
            'SUI': 'sui',

            # Additional tokens that might be in your portfolio
            'XRP': 'ripple',
            'DOGE': 'dogecoin',
            'SHIB': 'shiba-inu',
            'LTC': 'litecoin',
            'TRX': 'tron',
            'XLM': 'stellar',
            'VET': 'vechain',
            'FIL': 'filecoin',
            'THETA': 'theta-token',
            'GRT': 'the-graph',
            'CRV': 'curve-dao-token',
            'MKR': 'maker',
            'COMP': 'compound-governance-token',
            'SNX': 'synthetix-network-token',
            'YFI': 'yearn-finance',
            'SUSHI': 'sushi',
            '1INCH': '1inch',
            'BAT': 'basic-attention-token',
            'ZRX': '0x',
            'KNC': 'kyber-network-crystal',
            'BAL': 'balancer',
            'OCEAN': 'ocean-protocol',
            'RSR': 'reserve-rights-token',
            'BAND': 'band-protocol',
            'REN': 'republic-protocol',
            'KAVA': 'kava',
            'PERP': 'perpetual-protocol',
            'RUNE': 'thorchain',
            'CELO': 'celo',
            'CHZ': 'chiliz',
            'HOT': 'holotoken',
            'CELR': 'celer-network',
            'ALPHA': 'alpha-finance',
            'AKRO': 'akropolis',
            'AUDIO': 'audius',
            'BADGER': 'badger-dao',
            'DYDX': 'dydx',
            'ENS': 'ethereum-name-service',
            'FORTH': 'ampleforth-governance-token',
            'GTC': 'gitcoin',
            'ICP': 'internet-computer',
            'IMX': 'immutable-x',
            'INJ': 'injective-protocol',
            'KEEP': 'keep-network',
            'LRC': 'loopring',
            'MASK': 'mask-network',
            'MIR': 'mirror-protocol',
            'MLN': 'melon',
            'NKN': 'nkn',
            'NMR': 'numeraire',
            'NU': 'nucypher',
            'OGN': 'origin-protocol',
            'OMG': 'omisego',
            'OXT': 'orchid-protocol',
            'PAXG': 'pax-gold',
            'PLU': 'pluton',
            'POLY': 'polymath',
            'POWR': 'power-ledger',
            'QNT': 'quant-network',
            'RAD': 'radicle',
            'RAI': 'rai',
            'RGT': 'rari-governance-token',
            'RLC': 'iexec-rlc',
            'RLY': 'rally-2',
            'SKL': 'skale',
            'SPELL': 'spell-token',
            'STORJ': 'storj',
            'SUPER': 'superfarm',
            'TRIBE': 'tribe-2',
            'TRU': 'truefi',
            'UMA': 'uma',
            'UNFI': 'unifi-protocol-dao',
            'WBTC': 'wrapped-bitcoin',
            'XCN': 'chain-2',
            'XTZ': 'tezos',
            'ZEN': 'horizen',
        }

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call

        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_api_call = time.time()

    @rate_limit(calls_per_minute=50)
    def _make_api_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make rate-limited API request."""
        try:
            response = self.coingecko_client.get(endpoint, params=params)
            return response
        except Exception as e:
            if "429" in str(e):
                logger.warning("Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                # Retry once after waiting
                return self.coingecko_client.get(endpoint, params=params)
            raise

    def fetch_current_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Fetch current prices for multiple symbols with rate limiting."""
        prices = {}

        # Handle stablecoins
        stablecoins = {'USDT', 'USDC', 'UST', 'DAI', 'BUSD'}
        for symbol in symbols:
            if symbol in stablecoins:
                prices[symbol] = Decimal('1.0')
            elif symbol == 'USD':
                prices[symbol] = Decimal('1.0')

        # Filter out already handled symbols
        symbols_to_fetch = [s for s in symbols if s not in prices]

        # Filter out USD and check cache first
        symbols = [s for s in symbols if s != 'USD']

        for symbol in symbols:
            cached_price = self.cache.get_price(symbol)
            if cached_price is not None:
                prices[symbol] = Decimal(str(cached_price))
                logger.debug(f"Using cached price for {symbol}: {cached_price}")

        # Fetch missing prices
        missing_symbols = [s for s in symbols if s not in prices]

        if missing_symbols:
            # Batch symbols to reduce API calls (CoinGecko allows up to 250 IDs per call)
            batch_size = 50  # Conservative batch size

            for i in range(0, len(missing_symbols), batch_size):
                batch = missing_symbols[i:i + batch_size]

                # Convert symbols to CoinGecko IDs
                coin_ids = []
                symbol_to_id_map = {}

                for symbol in batch:
                    if symbol in self.symbol_map:
                        coin_id = self.symbol_map[symbol]
                        coin_ids.append(coin_id)
                        symbol_to_id_map[coin_id] = symbol
                    else:
                        logger.warning(f"Unknown symbol: {symbol}")

                if coin_ids:
                    # Fetch from CoinGecko
                    try:
                        logger.info(f"Fetching prices for {len(coin_ids)} coins...")

                        response = self._make_api_request(
                            "simple/price",
                            params={
                                'ids': ','.join(coin_ids),
                                'vs_currencies': 'usd',
                                'include_24hr_change': 'true'
                            }
                        )

                        # Map back to symbols
                        for coin_id, data in response.items():
                            if coin_id in symbol_to_id_map:
                                symbol = symbol_to_id_map[coin_id]
                                price = data.get('usd')
                                if price:
                                    prices[symbol] = Decimal(str(price))
                                    self.cache.set_price(symbol, price)
                                    logger.debug(f"Fetched price for {symbol}: ${price}")

                    except Exception as e:
                        logger.error(f"Failed to fetch prices for batch: {e}")
                        # Continue with next batch instead of failing completely
                        continue

        # Always set USD to 1
        prices['USD'] = Decimal('1.0')

        return prices

    def fetch_historical_price(self, symbol: str, date: datetime) -> Optional[Decimal]:
        """Fetch historical price for a specific date with rate limiting."""
        if symbol == 'USD':
            return Decimal('1.0')

        if symbol not in self.symbol_map:
            logger.warning(f"Unknown symbol: {symbol}")
            return None

        coin_id = self.symbol_map[symbol]
        date_str = date.strftime("%d-%m-%Y")

        # Check cache first
        cache_key = f"{symbol}_{date_str}"
        cached_price = self.cache.get_price(cache_key)
        if cached_price is not None:
            return Decimal(str(cached_price))

        try:
            logger.debug(f"Fetching historical price for {symbol} on {date_str}")

            response = self._make_api_request(
                f"coins/{coin_id}/history",
                params={'date': date_str}
            )

            price = response.get('market_data', {}).get('current_price', {}).get('usd')
            if price:
                price_decimal = Decimal(str(price))
                # Cache historical price
                self.cache.set_price(cache_key, float(price_decimal))
                return price_decimal

        except Exception as e:
            logger.error(f"Failed to fetch historical price for {symbol} on {date}: {e}")

        return None

    def get_supported_symbols(self) -> List[str]:
        """Get list of all supported symbols."""
        return list(self.symbol_map.keys())

    def is_symbol_supported(self, symbol: str) -> bool:
        """Check if a symbol is supported."""
        return symbol in self.symbol_map or symbol == 'USD'
