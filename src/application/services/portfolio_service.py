# src/application/services/portfolio_service.py

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd

from src.core.entities.portfolio import Portfolio
from src.core.entities.transaction import Transaction, TransactionType
from src.application.services.transaction_processor import TransactionProcessor
from src.application.services.metrics_calculator import MetricsCalculator, logger
from src.application.services.price_service import PriceService
from src.infrastructure.cache.price_cache import PriceCache


class PortfolioService:
    """
    Main application service that orchestrates portfolio operations.

    This service acts as the primary interface between the presentation layer
    and the domain/infrastructure layers.
    """

    def __init__(self,
                 data_path: str = "data/",
                 cache_path: str = "data/cache/",
                 cost_basis_method: str = "FIFO"):

        self.data_path = Path(data_path)
        self.cache_path = Path(cache_path)
        self.cost_basis_method = cost_basis_method

        # Initialize services
        self.transaction_processor = TransactionProcessor()
        self.metrics_calculator = MetricsCalculator(benchmark_asset='BTC', risk_free_rate=0.04248)
        self.price_service = PriceService()
        self.price_cache = PriceCache(cache_path)

        # Portfolio instance
        self.portfolio = None

        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def initialize_portfolio(self, csv_file_path: str) -> Dict[str, any]:
        """Initialize portfolio from CSV file."""
        try:
            # Parse transactions
            print("Parsing transactions from CSV...")
            transactions = self.transaction_processor.parse_csv_transactions(csv_file_path)

            # Create portfolio
            self.portfolio = Portfolio(
                name="Crypto Portfolio",
                cost_basis_method=self.cost_basis_method
            )

            # Process transactions
            print(f"Processing {len(transactions)} transactions...")
            results = self.transaction_processor.process_transactions_to_portfolio(
                transactions, self.portfolio
            )

            # Update current prices
            print("Fetching current prices...")
            self._update_current_prices()

            # Take initial snapshot
            self.portfolio.take_snapshot()

            # Save portfolio state
            self._save_portfolio_state()

            # Generate summary
            summary = {
                'total_transactions': len(transactions),
                'processed': results['processed'],
                'errors': len(results['errors']),
                'parsing_errors': len(self.transaction_processor.errors),
                'realized_trades': len(results['realized_gains']),
                'current_positions': len([p for p in self.portfolio.positions.values()
                                          if p.current_amount > 0]),
                'total_value': float(self.portfolio.get_total_value()),
                'net_invested': float(self.portfolio.total_deposits - self.portfolio.total_withdrawals)
            }

            print("\nPortfolio initialization complete!")
            print(f"Processed: {summary['processed']} transactions")
            print(f"Current positions: {summary['current_positions']}")
            print(f"Total value: ${summary['total_value']:,.2f}")

            return {
                'success': True,
                'summary': summary,
                'errors': results['errors'][:10],  # First 10 errors
                'parsing_errors': self.transaction_processor.errors[:10]
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def load_portfolio(self) -> bool:
        """Load portfolio from saved state."""
        portfolio_file = self.cache_path / "portfolio_state.pkl"

        if portfolio_file.exists():
            try:
                with open(portfolio_file, 'rb') as f:
                    self.portfolio = pickle.load(f)
                return True
            except Exception as e:
                print(f"Error loading portfolio: {e}")
                return False
        return False

    def _save_portfolio_state(self):
        """Save portfolio state to disk."""
        portfolio_file = self.cache_path / "portfolio_state.pkl"

        try:
            with open(portfolio_file, 'wb') as f:
                pickle.dump(self.portfolio, f)
        except Exception as e:
            print(f"Error saving portfolio: {e}")

    def _update_current_prices(self):
        """Update current prices for all assets."""
        if not self.portfolio:
            return

        # Get list of assets needing prices
        assets = [asset for asset, pos in self.portfolio.positions.items()
                  if asset not in ['USD', 'USDC', 'USDT', 'DAI', 'BUSD'] and pos.current_amount > 0]

        # Fetch prices (with caching)
        prices = {}
        for asset in assets:
            price = self.price_cache.get_price(asset)
            if price is None:
                # Fetch from API
                price = self.price_service.get_current_price(asset)
                if price:
                    self.price_cache.set_price(asset, price)
                    prices[asset] = Decimal(str(price))
            else:
                prices[asset] = Decimal(str(price))

        # Update portfolio
        self.portfolio.update_prices(prices)

    def update_portfolio(self) -> Dict[str, any]:
        """Update portfolio with latest prices and take snapshot."""
        if not self.portfolio:
            return {'success': False, 'error': 'Portfolio not initialized'}

        try:
            # Update prices
            self._update_current_prices()

            # Take snapshot
            self.portfolio.take_snapshot()

            # Save state
            self._save_portfolio_state()

            return {
                'success': True,
                'total_value': float(self.portfolio.get_total_value()),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_portfolio(self) -> Optional[Portfolio]:
        """Get current portfolio instance."""
        return self.portfolio

    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Get comprehensive portfolio metrics."""
        if not self.portfolio:
            return {}

        # Calculate metrics with fixed date range (Jul 1, 2023 - Feb 23, 2025)
        logger.info("Calculating portfolio metrics for date range: Jul 1, 2023 - Feb 23, 2025")

        # The metrics calculator should already have the correct dates set in __init__
        # Just call calculate_metrics
        metrics = self.metrics_calculator.calculate_metrics(self.portfolio)

        return metrics

    def get_position_details(self, asset: str) -> Dict[str, any]:
        """Get detailed information about a specific position."""
        if not self.portfolio or asset not in self.portfolio.positions:
            return {}

        position = self.portfolio.positions[asset]
        metrics = self.metrics_calculator.calculate_metrics(position)

        # Add transaction history
        metrics['transactions'] = [
            {
                'timestamp': tx.timestamp.isoformat(),
                'type': tx.type.value,
                'amount': float(tx.amount),
                'price': float(tx.price_usd) if tx.price_usd else None,
                'total': float(tx.total_usd) if tx.total_usd else None,
                'fee': float(tx.fee_usd) if tx.fee_usd else None
            }
            for tx in position.transactions
        ]

        # Add cost basis lots
        metrics['cost_basis_lots'] = [
            {
                'amount': float(lot.amount),
                'cost_per_unit': float(lot.cost_per_unit),
                'acquisition_date': lot.acquisition_date.isoformat(),
                'total_cost': float(lot.total_cost)
            }
            for lot in position.cost_basis_lots
        ]

        return metrics

    def generate_tax_report(self, year: int) -> Dict[str, any]:
        """Generate tax report for a specific year."""
        if not self.portfolio:
            return {}

        # Filter transactions by year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        realized_gains = []

        # Collect all realized gains/losses
        for position in list(self.portfolio.positions.values()) + self.portfolio.closed_positions:
            for tx in position.transactions:
                if (tx.type.is_disposal() and
                        start_date <= tx.timestamp <= end_date and
                        tx.realized_gain_loss is not None):
                    realized_gains.append({
                        'date': tx.timestamp,
                        'asset': tx.asset,
                        'amount': float(tx.amount),
                        'proceeds': float(tx.get_effective_cost()),
                        'cost_basis': float(tx.cost_basis) if tx.cost_basis else 0,
                        'gain_loss': float(tx.realized_gain_loss),
                        'holding_period': 'long' if (tx.timestamp - tx.acquisition_date).days > 365 else 'short'
                    })

        # Sort by date
        realized_gains.sort(key=lambda x: x['date'])

        # Calculate totals
        short_term_gains = sum(
            g['gain_loss'] for g in realized_gains if g['holding_period'] == 'short' and g['gain_loss'] > 0)
        short_term_losses = sum(
            g['gain_loss'] for g in realized_gains if g['holding_period'] == 'short' and g['gain_loss'] < 0)
        long_term_gains = sum(
            g['gain_loss'] for g in realized_gains if g['holding_period'] == 'long' and g['gain_loss'] > 0)
        long_term_losses = sum(
            g['gain_loss'] for g in realized_gains if g['holding_period'] == 'long' and g['gain_loss'] < 0)

        return {
            'year': year,
            'transactions': realized_gains,
            'summary': {
                'short_term_gains': short_term_gains,
                'short_term_losses': abs(short_term_losses),
                'long_term_gains': long_term_gains,
                'long_term_losses': abs(long_term_losses),
                'net_short_term': short_term_gains + short_term_losses,
                'net_long_term': long_term_gains + long_term_losses,
                'total_gain_loss': short_term_gains + short_term_losses + long_term_gains + long_term_losses
            }
        }

    def export_portfolio_data(self, format: str = 'json') -> str:
        """Export portfolio data in various formats."""
        if not self.portfolio:
            return ""

        data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'portfolio_name': self.portfolio.name,
                'cost_basis_method': self.portfolio.cost_basis_method,
                'base_currency': self.portfolio.base_currency
            },
            'summary': {
                'total_value': float(self.portfolio.get_total_value()),
                'net_invested': float(self.portfolio.total_deposits - self.portfolio.total_withdrawals),
                'total_return': float(self.portfolio.get_total_value() - (
                            self.portfolio.total_deposits - self.portfolio.total_withdrawals)),
                'num_positions': len([p for p in self.portfolio.positions.values() if p.current_amount > 0]),
                'num_transactions': sum(len(p.transactions) for p in self.portfolio.positions.values())
            },
            'positions': [
                self.metrics_calculator.calculate_metrics(pos)
                for pos in self.portfolio.positions.values()
                if pos.current_amount > 0
            ],
            'metrics': self.get_portfolio_metrics(),
            'asset_allocation': self.portfolio.get_asset_allocation()
        }

        if format == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format == 'csv':
            # Convert positions to DataFrame
            df = pd.DataFrame(data['positions'])
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def reconcile_portfolio(self) -> Dict[str, any]:
        """Perform portfolio reconciliation and validation."""
        if not self.portfolio:
            return {}

        issues = []

        # Check for negative balances
        for asset, position in self.portfolio.positions.items():
            if position.current_amount < 0:
                issues.append({
                    'type': 'negative_balance',
                    'asset': asset,
                    'amount': float(position.current_amount)
                })

        # Check for missing prices
        for asset, position in self.portfolio.positions.items():
            if position.current_amount > 0 and not position.current_price:
                issues.append({
                    'type': 'missing_price',
                    'asset': asset,
                    'amount': float(position.current_amount)
                })

        # Check for orphaned transactions
        all_transactions = []
        for position in list(self.portfolio.positions.values()) + self.portfolio.closed_positions:
            all_transactions.extend(position.transactions)

        # Check for unmatched conversions
        unmatched = [tx for tx in all_transactions
                     if tx.type in [TransactionType.CONVERT_FROM, TransactionType.CONVERT_TO]
                     and not tx.matched_transaction_id]

        if unmatched:
            issues.append({
                'type': 'unmatched_conversions',
                'count': len(unmatched),
                'transactions': [tx.transaction_id for tx in unmatched[:5]]
            })

        return {
            'issues': issues,
            'is_valid': len(issues) == 0,
            'timestamp': datetime.now().isoformat()
        }

    def get_transfer_summary(self) -> Dict[str, Any]:
        """Get summary of transfers and cold storage."""
        if not self.portfolio:
            return {}

        transfers_out = {}
        transfers_in = {}

        for position in self.portfolio.positions.values():
            for tx in position.transactions:
                if tx.type.value in ['Send', 'Transfer Out']:
                    if tx.asset not in transfers_out:
                        transfers_out[tx.asset] = Decimal('0')
                    transfers_out[tx.asset] += tx.amount
                elif tx.type.value in ['Receive', 'Transfer In']:
                    if tx.asset not in transfers_in:
                        transfers_in[tx.asset] = Decimal('0')
                    transfers_in[tx.asset] += tx.amount

        # Calculate net transfers (negative means more went out than came back)
        net_transfers = {}
        all_assets = set(transfers_out.keys()) | set(transfers_in.keys())

        for asset in all_assets:
            out_amount = transfers_out.get(asset, Decimal('0'))
            in_amount = transfers_in.get(asset, Decimal('0'))
            net = in_amount - out_amount

            if abs(net) > Decimal('0.0001'):  # Only show significant differences
                net_transfers[asset] = {
                    'transferred_out': float(out_amount),
                    'transferred_in': float(in_amount),
                    'net': float(net),
                    'likely_in_cold_storage': float(out_amount - in_amount) if out_amount > in_amount else 0
                }

        return {
            'assets_with_transfers': net_transfers,
            'total_assets_in_cold_storage': len([a for a in net_transfers.values() if a['likely_in_cold_storage'] > 0]),
            'estimated_cold_storage_value': sum(
                a['likely_in_cold_storage'] * float(
                    self.portfolio.positions.get(asset, type('', (), {'current_price': 0})()).current_price or 0)
                for asset, a in net_transfers.items()
            )
        }
