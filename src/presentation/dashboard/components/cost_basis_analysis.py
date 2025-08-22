# src/presentation/dashboard/components/cost_basis_analysis.py

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any
import numpy as np

from src.core.entities.portfolio import Portfolio


def create_cost_basis_charts(portfolio: Portfolio) -> go.Figure:
    """Create cost basis analysis charts."""

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Top 10 Positions by Unrealized P&L',
            'Monthly Realized Gains/Losses',
            'Position Size vs Cost Basis',
            'Transaction Type Distribution'
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "pie"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )

    # 1. Top positions by unrealized P&L
    positions_data = []
    for asset, position in portfolio.positions.items():
        if position.current_amount > 0 and asset != portfolio.base_currency:
            positions_data.append({
                'asset': asset,
                'unrealized_pnl': float(position.get_unrealized_pnl()),
                'unrealized_pct': float(position.get_unrealized_pnl_percent())
            })

    # Sort and get top 10
    positions_data.sort(key=lambda x: abs(x['unrealized_pnl']), reverse=True)
    top_positions = positions_data[:10]

    if top_positions:
        assets = [p['asset'] for p in top_positions]
        pnl_values = [p['unrealized_pnl'] for p in top_positions]
        pnl_pcts = [p['unrealized_pct'] for p in top_positions]
        colors = ['#10B981' if pnl > 0 else '#EF4444' for pnl in pnl_values]

        fig.add_trace(
            go.Bar(
                x=pnl_values,
                y=assets,
                orientation='h',
                marker_color=colors,
                text=[f"${pnl:,.0f} ({pct:+.1f}%)" for pnl, pct in zip(pnl_values, pnl_pcts)],
                textposition='auto',
                hovertemplate='%{y}: $%{x:,.2f}<br>%{text}<extra></extra>'
            ),
            row=1, col=1
        )

    # 2. Monthly realized gains/losses
    monthly_realized = _calculate_monthly_realized(portfolio)

    if monthly_realized:
        months = list(monthly_realized.keys())
        gains = [month_data['gains'] for month_data in monthly_realized.values()]
        losses = [month_data['losses'] for month_data in monthly_realized.values()]

        fig.add_trace(
            go.Bar(
                x=months,
                y=gains,
                name='Gains',
                marker_color='#10B981',
                hovertemplate='%{x}<br>Gains: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=2
        )

        fig.add_trace(
            go.Bar(
                x=months,
                y=losses,
                name='Losses',
                marker_color='#EF4444',
                hovertemplate='%{x}<br>Losses: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=2
        )

    # 3. Position size vs cost basis (log scale)
    position_scatter_data = []
    for asset, position in portfolio.positions.items():
        if position.current_amount > 0 and asset != portfolio.base_currency:
            position_scatter_data.append({
                'asset': asset,
                'cost_basis': float(position.get_average_cost()),
                'amount': float(position.current_amount),
                'value': float(position.get_current_value())
            })

    if position_scatter_data:
        fig.add_trace(
            go.Scatter(
                x=[p['cost_basis'] for p in position_scatter_data],
                y=[p['amount'] for p in position_scatter_data],
                mode='markers+text',
                marker=dict(
                    size=[np.sqrt(p['value']) / 10 for p in position_scatter_data],
                    color='#3B82F6',
                    opacity=0.6
                ),
                text=[p['asset'] for p in position_scatter_data],
                textposition='top center',
                hovertemplate='%{text}<br>Cost: $%{x:,.2f}<br>Amount: %{y:,.4f}<extra></extra>'
            ),
            row=2, col=1
        )

    # 4. Transaction type distribution
    tx_counts = _count_transaction_types(portfolio)

    if tx_counts:
        fig.add_trace(
            go.Pie(
                labels=list(tx_counts.keys()),
                values=list(tx_counts.values()),
                hole=0.4,
                marker=dict(
                    colors=['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']
                ),
                textinfo='label+percent',
                hovertemplate='%{label}<br>Count: %{value}<br>%{percent}<extra></extra>'
            ),
            row=2, col=2
        )

    # Update layout
    fig.update_xaxes(gridcolor='#374151', zeroline=False)
    fig.update_yaxes(gridcolor='#374151', zeroline=False)

    # Log scale for position scatter
    fig.update_xaxes(type="log", row=2, col=1, title="Average Cost (USD)")
    fig.update_yaxes(type="log", row=2, col=1, title="Amount Held")

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='#1F2937',
        paper_bgcolor='#1F2937',
        font=dict(color='#F3F4F6'),
        showlegend=False,
        height=600,
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig


def _calculate_monthly_realized(portfolio: Portfolio) -> Dict[str, Dict[str, float]]:
    """Calculate realized gains/losses by month."""
    monthly_data = {}

    # Collect all realized trades
    for position in list(portfolio.positions.values()) + portfolio.closed_positions:
        for tx in position.transactions:
            if tx.realized_gain_loss is not None:
                month_key = tx.timestamp.strftime('%Y-%m')

                if month_key not in monthly_data:
                    monthly_data[month_key] = {'gains': 0, 'losses': 0}

                if tx.realized_gain_loss > 0:
                    monthly_data[month_key]['gains'] += float(tx.realized_gain_loss)
                else:
                    monthly_data[month_key]['losses'] += abs(float(tx.realized_gain_loss))

    return dict(sorted(monthly_data.items()))


def _count_transaction_types(portfolio: Portfolio) -> Dict[str, int]:
    """Count transactions by type."""
    tx_counts = {}

    for position in list(portfolio.positions.values()) + portfolio.closed_positions:
        for tx in position.transactions:
            tx_type = tx.type.value

            # Simplify transaction types for display
            if tx_type in ['Convert (from)', 'Convert (to)']:
                tx_type = 'Convert'
            elif tx_type in ['Reward / Bonus', 'Staking', 'Interest', 'Airdrop']:
                tx_type = 'Rewards'

            tx_counts[tx_type] = tx_counts.get(tx_type, 0) + 1

    return tx_counts
