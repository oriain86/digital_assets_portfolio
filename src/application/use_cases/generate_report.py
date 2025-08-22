# src/application/use_cases/generate_report.py

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import logging
import numpy as np

from src.core.entities.portfolio import Portfolio
from src.application.use_cases.calculate_metrics import CalculateMetricsUseCase

logger = logging.getLogger(__name__)


class GenerateReportUseCase:
    """
    Use case for generating various types of portfolio reports.
    """

    def __init__(self):
        self.metrics_calculator = CalculateMetricsUseCase()
        self.report_templates = {
            'summary': self._generate_summary_report,
            'detailed': self._generate_detailed_report,
            'tax': self._generate_tax_report,
            'performance': self._generate_performance_report,
            'positions': self._generate_positions_report
        }

    def execute(self,
                portfolio: Portfolio,
                report_type: str = 'summary',
                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a portfolio report.

        Args:
            portfolio: Portfolio to report on
            report_type: Type of report (summary, detailed, tax, performance, positions)
            options: Report configuration options

        Returns:
            Report data dictionary
        """
        options = options or {}

        logger.info(f"Generating {report_type} report for {portfolio.name}")

        if report_type not in self.report_templates:
            return {
                'success': False,
                'error': f'Unknown report type: {report_type}'
            }

        try:
            # Generate the report
            report_generator = self.report_templates[report_type]
            report_data = report_generator(portfolio, options)

            # Add metadata
            report_data['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'report_type': report_type,
                'portfolio_name': portfolio.name,
                'version': '1.0'
            }

            # Export if requested
            if options.get('export_path'):
                self._export_report(report_data, options['export_path'], options.get('format', 'json'))

            return {
                'success': True,
                'report': report_data
            }

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_summary_report(self, portfolio: Portfolio, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary report with key metrics and current positions."""
        # Calculate metrics
        metrics_result = self.metrics_calculator.execute(portfolio, {
            'include_rolling': False,
            'include_correlations': False,
            'include_position_details': True
        })

        metrics = metrics_result.get('metrics', {}).get('basic', {})
        summary = metrics_result.get('summary', {})

        return {
            'overview': {
                'total_value': summary.get('total_value', 0),
                'total_invested': summary.get('total_invested', 0),
                'total_return': summary.get('total_return', 0),
                'total_return_percent': summary.get('total_return_percent', 0),
                'num_positions': len([p for p in portfolio.positions.values() if p.current_amount > 0])
            },
            'performance': {
                'sharpe_ratio': metrics.get('sharpe_ratio'),
                'max_drawdown': metrics.get('max_drawdown'),
                'volatility': metrics.get('volatility'),
                'win_rate': metrics.get('win_rate')
            },
            'top_positions': self._get_top_positions(portfolio, 5),
            'recent_transactions': self._get_recent_transactions(portfolio, 10)
        }

    def _generate_detailed_report(self, portfolio: Portfolio, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive detailed report."""
        # Calculate all metrics
        metrics_result = self.metrics_calculator.execute(portfolio, {
            'include_rolling': True,
            'include_correlations': True,
            'include_position_details': True,
            'include_tax_preview': True,
            'include_performance_attribution': True
        })

        return {
            'metrics': metrics_result.get('metrics', {}),
            'positions': metrics_result.get('positions', []),
            'correlations': metrics_result.get('correlations', {}),
            'rolling_metrics': metrics_result.get('rolling_metrics', {}),
            'tax_preview': metrics_result.get('tax_preview', {}),
            'attribution': metrics_result.get('attribution', {}),
            'transactions': self._get_all_transactions(portfolio),
            'monthly_performance': portfolio.get_performance_by_period('monthly')
        }

    def _generate_tax_report(self, portfolio: Portfolio, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a tax-focused report."""
        year = options.get('tax_year', datetime.now().year)

        realized_transactions = []
        short_term_gains = 0
        short_term_losses = 0
        long_term_gains = 0
        long_term_losses = 0

        # Collect all realized gains/losses for the year
        for position in list(portfolio.positions.values()) + portfolio.closed_positions:
            for tx in position.transactions:
                if (hasattr(tx, 'realized_gain_loss') and
                        tx.realized_gain_loss is not None and
                        tx.timestamp.year == year):

                    tx_data = {
                        'date': tx.timestamp.isoformat(),
                        'asset': tx.asset,
                        'amount': float(tx.amount),
                        'proceeds': float(tx.get_effective_cost()),
                        'cost_basis': float(tx.cost_basis) if hasattr(tx, 'cost_basis') else 0,
                        'gain_loss': float(tx.realized_gain_loss),
                        'holding_period': 'long' if hasattr(tx,
                                                            'holding_period_days') and tx.holding_period_days > 365 else 'short'
                    }

                    realized_transactions.append(tx_data)

                    if tx_data['holding_period'] == 'long':
                        if tx_data['gain_loss'] > 0:
                            long_term_gains += tx_data['gain_loss']
                        else:
                            long_term_losses += abs(tx_data['gain_loss'])
                    else:
                        if tx_data['gain_loss'] > 0:
                            short_term_gains += tx_data['gain_loss']
                        else:
                            short_term_losses += abs(tx_data['gain_loss'])

        return {
            'tax_year': year,
            'summary': {
                'short_term_gains': short_term_gains,
                'short_term_losses': short_term_losses,
                'net_short_term': short_term_gains - short_term_losses,
                'long_term_gains': long_term_gains,
                'long_term_losses': long_term_losses,
                'net_long_term': long_term_gains - long_term_losses,
                'total_net': (short_term_gains - short_term_losses) + (long_term_gains - long_term_losses)
            },
            'transactions': sorted(realized_transactions, key=lambda x: x['date']),
            'form_8949_data': self._prepare_form_8949_data(realized_transactions)
        }

    def _generate_performance_report(self, portfolio: Portfolio, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a performance-focused report."""
        period = options.get('period', 'monthly')

        return {
            'period_performance': portfolio.get_performance_by_period(period),
            'cumulative_returns': self._calculate_cumulative_returns(portfolio),
            'risk_metrics': self._calculate_risk_metrics(portfolio),
            'benchmark_comparison': self._compare_to_benchmark(portfolio, options.get('benchmark', 'BTC'))
        }

    def _generate_positions_report(self, portfolio: Portfolio, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a positions-focused report."""
        positions_data = []

        for asset, position in portfolio.positions.items():
            if position.current_amount > 0:
                pos_data = {
                    'asset': asset,
                    'amount': float(position.current_amount),
                    'average_cost': float(position.get_average_cost()),
                    'current_value': float(position.get_current_value()),
                    'unrealized_pnl': float(position.get_unrealized_pnl()),
                    'unrealized_pnl_percent': float(position.get_unrealized_pnl_percent()),
                    'realized_pnl': float(position.get_total_realized_pnl()),
                    'total_pnl': float(position.get_unrealized_pnl() + position.get_total_realized_pnl()),
                    'allocation_percent': self._calculate_allocation(position, portfolio),
                    'num_transactions': len(position.transactions),
                    'first_purchase': min(tx.timestamp for tx in position.transactions).isoformat(),
                    'cost_basis_lots': [
                        {
                            'amount': float(lot.amount),
                            'cost_per_unit': float(lot.cost_per_unit),
                            'acquisition_date': lot.acquisition_date.isoformat(),
                            'total_cost': float(lot.total_cost)
                        }
                        for lot in position.cost_basis_lots
                    ]
                }
                positions_data.append(pos_data)

        # Sort by current value
        positions_data.sort(key=lambda x: x['current_value'], reverse=True)

        return {
            'positions': positions_data,
            'total_positions': len(positions_data),
            'concentration_risk': self._calculate_concentration_risk(portfolio)
        }

    def _get_top_positions(self, portfolio: Portfolio, limit: int) -> List[Dict[str, Any]]:
        """Get top positions by value."""
        positions = []

        for asset, position in portfolio.positions.items():
            if position.current_amount > 0 and asset != portfolio.base_currency:
                positions.append({
                    'asset': asset,
                    'value': float(position.get_current_value()),
                    'allocation': self._calculate_allocation(position, portfolio),
                    'unrealized_pnl_percent': float(position.get_unrealized_pnl_percent())
                })

        positions.sort(key=lambda x: x['value'], reverse=True)
        return positions[:limit]

    def _get_recent_transactions(self, portfolio: Portfolio, limit: int) -> List[Dict[str, Any]]:
        """Get most recent transactions."""
        all_transactions = []

        for position in portfolio.positions.values():
            for tx in position.transactions:
                all_transactions.append({
                    'date': tx.timestamp.isoformat(),
                    'type': tx.type.value,
                    'asset': tx.asset,
                    'amount': float(tx.amount),
                    'price': float(tx.price_usd) if tx.price_usd else None,
                    'total': float(tx.total_usd) if tx.total_usd else None
                })

        all_transactions.sort(key=lambda x: x['date'], reverse=True)
        return all_transactions[:limit]

    def _get_all_transactions(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """Get all transactions with full details."""
        all_transactions = []

        for position in list(portfolio.positions.values()) + portfolio.closed_positions:
            for tx in position.transactions:
                all_transactions.append(tx.to_dict())

        all_transactions.sort(key=lambda x: x['timestamp'])
        return all_transactions

    def _calculate_allocation(self, position, portfolio: Portfolio) -> float:
        """Calculate position allocation percentage."""
        total_value = portfolio.get_total_value()
        if total_value == 0:
            return 0.0
        return float(position.get_current_value() / total_value * 100)

    def _calculate_cumulative_returns(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """Calculate cumulative returns over time."""
        if not portfolio.snapshots:
            return []

        initial_value = float(portfolio.snapshots[0].total_value)
        cumulative_returns = []

        for snapshot in portfolio.snapshots:
            return_pct = (
                        (float(snapshot.total_value) - initial_value) / initial_value * 100) if initial_value > 0 else 0
            cumulative_returns.append({
                'date': snapshot.timestamp.isoformat(),
                'value': float(snapshot.total_value),
                'return_percent': return_pct
            })

        return cumulative_returns

    def _calculate_risk_metrics(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics."""
        if len(portfolio.daily_returns) < 2:
            return {}

        returns = [r[1] for r in portfolio.daily_returns]

        return {
            'daily_var_95': np.percentile(returns, 5),
            'daily_var_99': np.percentile(returns, 1),
            'downside_deviation': np.std([r for r in returns if r < 0]) * np.sqrt(365) if any(
                r < 0 for r in returns) else 0,
            'up_capture': len([r for r in returns if r > 0]) / len(returns) if returns else 0,
            'down_capture': len([r for r in returns if r < 0]) / len(returns) if returns else 0
        }

    def _compare_to_benchmark(self, portfolio: Portfolio, benchmark: str) -> Dict[str, Any]:
        """Compare portfolio performance to a benchmark asset."""
        # This is simplified - would need historical benchmark data
        return {
            'benchmark': benchmark,
            'note': 'Benchmark comparison requires historical price data'
        }

    def _calculate_concentration_risk(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Calculate concentration risk metrics."""
        allocations = []

        for asset, position in portfolio.positions.items():
            if position.current_amount > 0 and asset != portfolio.base_currency:
                allocation = self._calculate_allocation(position, portfolio)
                allocations.append(allocation)

        if not allocations:
            return {}

        allocations.sort(reverse=True)

        return {
            'top_position_weight': allocations[0] if allocations else 0,
            'top_3_weight': sum(allocations[:3]) if len(allocations) >= 3 else sum(allocations),
            'top_5_weight': sum(allocations[:5]) if len(allocations) >= 5 else sum(allocations),
            'herfindahl_index': sum(a ** 2 for a in allocations)  # Concentration measure
        }

    def _prepare_form_8949_data(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare data in Form 8949 format for tax reporting."""
        form_data = []

        for tx in transactions:
            form_data.append({
                'description': f"{tx['amount']} {tx['asset']}",
                'date_acquired': tx.get('acquisition_date', 'Various'),
                'date_sold': tx['date'],
                'proceeds': tx['proceeds'],
                'cost_basis': tx['cost_basis'],
                'gain_loss': tx['gain_loss'],
                'type': tx['holding_period']
            })

        return form_data

    def _export_report(self, report_data: Dict[str, Any], path: str, format: str):
        """Export report to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        elif format == 'csv':
            # Convert to CSV (simplified - would need proper implementation)
            import pandas as pd

            # Flatten the report data for CSV
            flattened = self._flatten_dict(report_data)
            df = pd.DataFrame([flattened])
            df.to_csv(output_path, index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Report exported to {output_path}")

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
