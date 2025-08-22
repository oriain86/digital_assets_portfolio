# src/presentation/dashboard/callbacks/update_callbacks.py

from dash.dependencies import Input, Output, State, ALL
import plotly.graph_objs as go
from datetime import datetime
import pandas as pd
import logging

from src.presentation.dashboard.components.portfolio_chart import create_portfolio_value_chart
from src.presentation.dashboard.components.rolling_metrics import create_rolling_metrics_chart
from src.presentation.dashboard.components.cost_basis_analysis import create_cost_basis_charts
from src.presentation.dashboard.components.metrics_cards import format_metric_value

logger = logging.getLogger(__name__)


def register_callbacks(app, portfolio_service):
    """Register all dashboard callbacks."""

    @app.callback(
        Output('portfolio-value-chart', 'figure'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_portfolio_chart(n_intervals):
        """Update main portfolio value chart."""
        try:
            portfolio = portfolio_service.get_portfolio()
            if portfolio:
                return create_portfolio_value_chart(portfolio)
            else:
                return _create_empty_figure("No portfolio data available")
        except Exception as e:
            logger.error(f"Error updating portfolio chart: {e}")
            return _create_empty_figure("Error loading portfolio data")

    @app.callback(
        Output('rolling-metrics-chart', 'figure'),
        [Input('rolling-window-selector', 'value'),
         Input('interval-component', 'n_intervals')]
    )
    def update_rolling_metrics(window_days, n_intervals):
        """Update rolling metrics chart based on selected window."""
        try:
            portfolio = portfolio_service.get_portfolio()
            metrics = portfolio_service.get_portfolio_metrics()

            if portfolio and metrics:
                rolling_metrics = metrics.get('rolling', {})
                return create_rolling_metrics_chart(portfolio, rolling_metrics, window_days)
            else:
                return _create_empty_figure("No metrics data available")
        except Exception as e:
            logger.error(f"Error updating rolling metrics: {e}")
            return _create_empty_figure("Error loading metrics")

    @app.callback(
        Output('cost-basis-chart', 'figure'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_cost_basis_charts(n_intervals):
        """Update cost basis analysis charts."""
        try:
            portfolio = portfolio_service.get_portfolio()
            if portfolio:
                return create_cost_basis_charts(portfolio)
            else:
                return _create_empty_figure("No portfolio data available")
        except Exception as e:
            logger.error(f"Error updating cost basis charts: {e}")
            return _create_empty_figure("Error loading data")

    @app.callback(
        [Output('positions-table', 'data'),
         Output('positions-table', 'style_data_conditional')],
        [Input('interval-component', 'n_intervals'),
         Input('positions-table', 'sort_by')]
    )
    def update_positions_table(n_intervals, sort_by):
        """Update positions table with sorting."""
        try:
            portfolio = portfolio_service.get_portfolio()
            if not portfolio:
                return [], []

            # Prepare positions data
            positions_data = []
            for asset, position in portfolio.positions.items():
                if position.current_amount > 0 and asset != 'USD':
                    positions_data.append({
                        'symbol': asset,
                        'amount': float(position.current_amount),
                        'avg_cost': float(position.get_average_cost()),
                        'current_price': float(position.current_price) if position.current_price else 0,
                        'total_cost': float(position.total_cost_basis),
                        'current_value': float(position.get_current_value()),
                        'unrealized_pnl': float(position.get_unrealized_pnl()),
                        'unrealized_pct': float(position.get_unrealized_pnl_percent())
                    })

            # Apply sorting if specified
            if sort_by:
                positions_data = sorted(
                    positions_data,
                    key=lambda x: x[sort_by[0]['column_id']],
                    reverse=sort_by[0]['direction'] == 'desc'
                )
            else:
                # Default sort by current value
                positions_data.sort(key=lambda x: x['current_value'], reverse=True)

            # Style conditions for coloring P&L
            style_conditions = [
                {
                    'if': {
                        'filter_query': '{unrealized_pnl} > 0',
                        'column_id': ['unrealized_pnl', 'unrealized_pct']
                    },
                    'color': '#10B981'
                },
                {
                    'if': {
                        'filter_query': '{unrealized_pnl} < 0',
                        'column_id': ['unrealized_pnl', 'unrealized_pct']
                    },
                    'color': '#EF4444'
                }
            ]

            return positions_data, style_conditions

        except Exception as e:
            logger.error(f"Error updating positions table: {e}")
            return [], []

    @app.callback(
        [Output('total-return-value', 'children'),
         Output('cagr-value', 'children'),
         Output('sharpe-ratio-value', 'children'),
         Output('sortino-ratio-value', 'children'),
         Output('max-drawdown-value', 'children'),
         Output('win-rate-value', 'children'),
         Output('daily-volatility-value', 'children'),
         Output('annual-volatility-value', 'children'),
         Output('calmar-ratio-value', 'children'),
         Output('profit-factor-value', 'children')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_metric_cards(n_intervals):
        """Update all metric card values."""
        try:
            metrics = portfolio_service.get_portfolio_metrics()
            basic = metrics.get('basic', {})

            # Format each metric
            total_return = format_metric_value(basic.get('total_return_percent', 0), 'return')
            cagr = format_metric_value(basic.get('cagr', 0) * 100 if basic.get('cagr') else 0, 'percent')
            sharpe = format_metric_value(basic.get('sharpe_ratio', 0), 'ratio')
            sortino = format_metric_value(basic.get('sortino_ratio', 0), 'ratio')
            max_dd = format_metric_value(basic.get('max_drawdown', 0) * 100, 'percent')
            win_rate = format_metric_value(basic.get('win_rate', 0) * 100, 'percent')
            daily_vol = format_metric_value(basic.get('volatility', 0) * 100 / (365 ** 0.5), 'percent')
            annual_vol = format_metric_value(basic.get('volatility', 0) * 100, 'percent')
            calmar = format_metric_value(basic.get('calmar_ratio', 0), 'ratio')
            profit_factor = format_metric_value(basic.get('profit_factor', 0), 'ratio')

            return (total_return, cagr, sharpe, sortino, max_dd,
                    win_rate, daily_vol, annual_vol, calmar, profit_factor)

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            return ('N/A',) * 10

    @app.callback(
        [Output('total-buys-value', 'children'),
         Output('total-sells-value', 'children'),
         Output('net-invested-value', 'children'),
         Output('current-cash-value', 'children'),
         Output('positions-count', 'children')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_transaction_summary(n_intervals):
        """Update transaction summary statistics."""
        try:
            portfolio = portfolio_service.get_portfolio()
            if not portfolio:
                return '0', '0', '$0.00', '$0.00', 'No positions'

            # Count transactions by type
            buy_count = 0
            sell_count = 0

            for position in list(portfolio.positions.values()) + portfolio.closed_positions:
                for tx in position.transactions:
                    if tx.type.value == 'Buy':
                        buy_count += 1
                    elif tx.type.value == 'Sell':
                        sell_count += 1

            # Calculate net invested and current cash
            net_invested = portfolio.total_deposits - portfolio.total_withdrawals
            current_cash = portfolio.cash_balance

            # Count active positions
            active_positions = len([p for p in portfolio.positions.values()
                                    if p.current_amount > 0 and p.asset != 'USD'])

            return (
                str(buy_count),
                str(sell_count),
                f"${net_invested:,.2f}",
                f"${current_cash:,.2f}",
                f"Still holding {active_positions} positions"
            )

        except Exception as e:
            logger.error(f"Error updating transaction summary: {e}")
            return '0', '0', '$0.00', '$0.00', 'Error loading data'

    @app.callback(
        [Output('realized-gains-table', 'data'),
         Output('total-realized-pnl', 'children')],
        [Input('interval-component', 'n_intervals'),
         Input('realized-gains-table', 'sort_by')]
    )
    def update_realized_gains(n_intervals, sort_by):
        """Update realized gains table."""
        try:
            portfolio = portfolio_service.get_portfolio()
            if not portfolio:
                return [], "Total Realized Gains/Losses: $0.00"

            # Collect all realized gains
            realized_trades = []
            total_realized = 0

            for position in list(portfolio.positions.values()) + portfolio.closed_positions:
                for tx in position.transactions:
                    if hasattr(tx, 'realized_gain_loss') and tx.realized_gain_loss is not None:
                        realized_trades.append({
                            'date': tx.timestamp.strftime('%Y-%m-%d'),
                            'symbol': tx.asset,
                            'amount': float(tx.amount),
                            'sale_price': float(tx.price_usd) if tx.price_usd else 0,
                            'cost_basis': float(tx.cost_basis) if hasattr(tx, 'cost_basis') else 0,
                            'realized_gain': float(tx.realized_gain_loss)
                        })
                        total_realized += float(tx.realized_gain_loss)

            # Apply sorting if specified
            if sort_by:
                realized_trades = sorted(
                    realized_trades,
                    key=lambda x: x[sort_by[0]['column_id']],
                    reverse=sort_by[0]['direction'] == 'desc'
                )
            else:
                # Default sort by date descending
                realized_trades.sort(key=lambda x: x['date'], reverse=True)

            # Limit to most recent 100 trades for performance
            realized_trades = realized_trades[:100]

            return realized_trades, f"Total Realized Gains/Losses: ${total_realized:,.2f}"

        except Exception as e:
            logger.error(f"Error updating realized gains: {e}")
            return [], "Error loading realized gains"

    @app.callback(
        Output('refresh-status', 'children'),
        [Input('refresh-button', 'n_clicks')],
        [State('refresh-status', 'children')]
    )
    def manual_refresh(n_clicks, current_status):
        """Handle manual refresh button."""
        if n_clicks:
            try:
                # Update prices
                result = portfolio_service.update_portfolio()
                if result['success']:
                    return f"✓ Last updated: {datetime.now().strftime('%H:%M:%S')}"
                else:
                    return f"⚠ Update failed: {result.get('error', 'Unknown error')}"
            except Exception as e:
                return f"⚠ Update error: {str(e)}"
        return current_status


def _create_empty_figure(message: str) -> go.Figure:
    """Create an empty figure with a message."""
    fig = go.Figure()
    fig.add_annotation(
        x=0.5, y=0.5,
        xref="paper", yref="paper",
        text=message,
        showarrow=False,
        font=dict(size=20, color='#9CA3AF'),
        xanchor='center', yanchor='middle'
    )
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='#1F2937',
        paper_bgcolor='#1F2937',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig
