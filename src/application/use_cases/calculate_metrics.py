# src/application/use_cases/calculate_metrics.py

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from src.core.entities.portfolio import Portfolio
from src.application.services.metrics_calculator import MetricsCalculator

logger = logging.getLogger(__name__)


class CalculateMetricsUseCase:
    """
    Use case for calculating portfolio metrics with various options and filters.
    """

    def __init__(self, benchmark_asset: str = 'BTC', risk_free_rate: float = 0.04248):
        self.calculator = MetricsCalculator(benchmark_asset=benchmark_asset, risk_free_rate=risk_free_rate)

    def execute(self,
                portfolio: Portfolio,
                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a portfolio.

        Args:
            portfolio: Portfolio to analyze
            options: Configuration options including:
                - benchmark_asset: str - Asset to calculate beta against (default: BTC)
                - include_monthly_breakdown: bool - Include detailed monthly returns
                - lookback_years: int - Years to look back (ignored - uses fixed date range)
                - full_history: bool - If True, calculates from all available data (for charts)

        Returns:
            Dictionary containing all calculated metrics
        """
        options = options or {}

        try:
            # Check if we should use full history (for charts) or fixed date range
            if options.get('full_history', False):
                # Temporarily set to use all available data
                original_start = self.calculator.start_date
                original_end = self.calculator.end_date
                self.calculator.start_date = datetime(2020, 1, 1)  # Far back enough
                self.calculator.end_date = datetime.now()

            # Calculate metrics
            date_range_str = f"{self.calculator.start_date.strftime('%b %d, %Y')} to {self.calculator.end_date.strftime('%b %d, %Y')}"
            logger.info(f"Calculating portfolio metrics for date range: {date_range_str}")
            metrics = self.calculator.calculate_metrics(portfolio)

            # Restore original dates if we used full history
            if options.get('full_history', False):
                self.calculator.start_date = original_start
                self.calculator.end_date = original_end

            # Structure the response
            results = {
                'calculated_at': datetime.now().isoformat(),
                'portfolio_name': portfolio.name,
                'date_range': date_range_str,
                'benchmark': self.calculator.benchmark_asset,
                'success': True,

                # Core metrics
                'performance': {
                    'total_return': metrics['total_return'],
                    'total_return_pct': metrics['total_return_pct'],
                    'annualized_return': metrics['annualized_return'],
                    'net_profit': metrics['net_profit'],
                    'current_value': metrics['current_value'],
                    'net_invested': metrics['net_invested'],
                    'total_fees': metrics.get('total_fees', 0)  # Add this line
                },

                # Risk metrics
                'risk': {
                    'sharpe_ratio': metrics['sharpe_ratio'],
                    'sortino_ratio': metrics['sortino_ratio'],
                    'max_drawdown': metrics['max_drawdown'],
                    'beta': metrics['beta']
                },

                # Trading statistics
                'trading': {
                    'win_rate': metrics['win_rate'],
                    'total_trades': metrics['total_trades'],
                    'winning_months_pct': metrics['winning_months_pct'],
                    'losing_months_pct': metrics['losing_months_pct']
                },

                # Time series for charts
                'time_series': metrics['time_series']
            }

            # Add monthly breakdown if requested
            if options.get('include_monthly_breakdown', False):
                results['monthly_returns'] = metrics.get('monthly_returns', [])

            # Add summary
            results['summary'] = self._generate_summary(metrics)

            return results

        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return {
                'success': False,
                'error': str(e),
                'performance': {},
                'risk': {},
                'trading': {}
            }

    def _generate_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of metrics."""

        # Determine portfolio health score based on multiple factors
        health_score = self._calculate_health_score(metrics)

        # Risk assessment
        risk_level = self._assess_risk_level(metrics)

        # Performance rating
        performance_rating = self._rate_performance(metrics)

        return {
            'health_score': health_score,  # 0-100
            'risk_level': risk_level,  # Low/Medium/High
            'performance_rating': performance_rating,  # Poor/Average/Good/Excellent
            'key_insights': self._generate_insights(metrics)
        }

    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall portfolio health score (0-100)."""
        score = 50.0  # Base score

        # Positive factors
        if metrics['sharpe_ratio'] > 1.5:
            score += 15
        elif metrics['sharpe_ratio'] > 1.0:
            score += 10
        elif metrics['sharpe_ratio'] > 0.5:
            score += 5

        if metrics['win_rate'] > 60:
            score += 10
        elif metrics['win_rate'] > 50:
            score += 5

        if metrics['annualized_return'] > 30:
            score += 15
        elif metrics['annualized_return'] > 15:
            score += 10
        elif metrics['annualized_return'] > 0:
            score += 5

        # Negative factors
        if metrics['max_drawdown'] > 50:
            score -= 20
        elif metrics['max_drawdown'] > 30:
            score -= 10
        elif metrics['max_drawdown'] > 20:
            score -= 5

        if metrics['beta'] > 2.0:
            score -= 10  # Very high volatility vs market
        elif metrics['beta'] > 1.5:
            score -= 5

        if metrics['losing_months_pct'] > 60:
            score -= 10
        elif metrics['losing_months_pct'] > 50:
            score -= 5

        # Ensure score is between 0 and 100
        return max(0, min(100, score))

    def _assess_risk_level(self, metrics: Dict[str, Any]) -> str:
        """Assess portfolio risk level based on metrics."""
        risk_score = 0

        # Max drawdown contribution
        if metrics['max_drawdown'] > 50:
            risk_score += 3
        elif metrics['max_drawdown'] > 30:
            risk_score += 2
        elif metrics['max_drawdown'] > 20:
            risk_score += 1

        # Beta contribution
        if metrics['beta'] > 2.0:
            risk_score += 2
        elif metrics['beta'] > 1.5:
            risk_score += 1

        # Sharpe ratio (inverse contribution)
        if metrics['sharpe_ratio'] < 0.5:
            risk_score += 1

        # Determine risk level
        if risk_score >= 4:
            return 'High'
        elif risk_score >= 2:
            return 'Medium'
        else:
            return 'Low'

    def _rate_performance(self, metrics: Dict[str, Any]) -> str:
        """Rate portfolio performance."""
        performance_score = 0

        # Annual return contribution
        if metrics['annualized_return'] > 50:
            performance_score += 3
        elif metrics['annualized_return'] > 25:
            performance_score += 2
        elif metrics['annualized_return'] > 10:
            performance_score += 1

        # Sharpe ratio contribution
        if metrics['sharpe_ratio'] > 2.0:
            performance_score += 2
        elif metrics['sharpe_ratio'] > 1.0:
            performance_score += 1

        # Win rate contribution
        if metrics['win_rate'] > 60:
            performance_score += 1

        # Determine rating
        if performance_score >= 5:
            return 'Excellent'
        elif performance_score >= 3:
            return 'Good'
        elif performance_score >= 1:
            return 'Average'
        else:
            return 'Poor'

    def _generate_insights(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate key insights from metrics."""
        insights = []

        # Performance insights
        if metrics['annualized_return'] > 25:
            insights.append(f"Strong performance with {metrics['annualized_return']:.1f}% annualized return")
        elif metrics['annualized_return'] < 0:
            insights.append(f"Negative returns of {metrics['annualized_return']:.1f}% annually")

        # Risk insights
        if metrics['max_drawdown'] > 40:
            insights.append(f"High risk with {metrics['max_drawdown']:.1f}% maximum drawdown")
        elif metrics['max_drawdown'] < 20:
            insights.append(f"Well-managed risk with only {metrics['max_drawdown']:.1f}% max drawdown")

        # Risk-adjusted return insights
        if metrics['sharpe_ratio'] > 1.5:
            insights.append(f"Excellent risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")
        elif metrics['sharpe_ratio'] < 0.5:
            insights.append(f"Poor risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")

        # Trading insights
        if metrics['win_rate'] > 60:
            insights.append(f"High win rate of {metrics['win_rate']:.1f}%")
        elif metrics['win_rate'] < 40:
            insights.append(f"Low win rate of {metrics['win_rate']:.1f}%")

        # Beta insights
        if metrics['beta'] > 1.5:
            insights.append(f"High volatility vs {self.calculator.benchmark_asset} (Beta: {metrics['beta']:.2f})")
        elif metrics['beta'] < 0.5:
            insights.append(f"Low correlation with {self.calculator.benchmark_asset} (Beta: {metrics['beta']:.2f})")

        return insights[:4]  # Return top 4 insights
