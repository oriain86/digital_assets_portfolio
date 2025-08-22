# src/presentation/dashboard/components/portfolio_chart.py

import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

from src.core.entities.portfolio import Portfolio


def create_portfolio_value_chart(portfolio: Portfolio) -> go.Figure:
    """Create the main portfolio value chart with area fill."""

    if not portfolio.snapshots:
        return _create_empty_chart("No data available")

    # Extract data
    dates = [s.timestamp for s in portfolio.snapshots]
    values = [float(s.total_value) for s in portfolio.snapshots]

    # Calculate cumulative deposits/withdrawals
    cumulative_deposits = []
    net_invested = 0

    for snapshot in portfolio.snapshots:
        # This is simplified - would need transaction history for exact calculation
        net_invested = float(portfolio.total_deposits - portfolio.total_withdrawals)
        cumulative_deposits.append(net_invested)

    # Create figure with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=('Portfolio Value (Excluding Deposits/Withdrawals)', None)
    )

    # Portfolio value line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#3B82F6', width=2),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)',
            hovertemplate='$%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )

    # Add cost basis line
    if cumulative_deposits:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cumulative_deposits,
                mode='lines',
                name='Net Deposits',
                line=dict(color='#F59E0B', width=1, dash='dot'),
                hovertemplate='$%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    # Add realized gains area
    if portfolio.snapshots:
        realized_gains = [float(s.realized_pnl) for s in portfolio.snapshots]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=realized_gains,
                mode='lines',
                name='Cumulative Realized Gains',
                line=dict(color='#10B981', width=1),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.1)',
                hovertemplate='$%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    # Calculate and add drawdown chart
    drawdowns = _calculate_drawdowns(values)

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[dd * 100 for dd in drawdowns],
            mode='lines',
            name='Drawdown %',
            line=dict(color='#EF4444', width=1),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.2)',
            hovertemplate='%{y:.2f}%<extra></extra>'
        ),
        row=2, col=1
    )

    # Update layout
    fig.update_xaxes(
        gridcolor='#374151',
        showgrid=True,
        row=2, col=1
    )

    fig.update_yaxes(
        title_text="Value (USD)",
        gridcolor='#374151',
        showgrid=True,
        tickformat='$,.0f',
        row=1, col=1
    )

    fig.update_yaxes(
        title_text="Drawdown (%)",
        gridcolor='#374151',
        showgrid=True,
        tickformat='.1f',
        row=2, col=1
    )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='#1F2937',
        paper_bgcolor='#1F2937',
        font=dict(color='#F3F4F6'),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        height=500
    )

    # Add range slider to bottom chart only
    fig.update_xaxes(
        rangeslider=dict(visible=True, thickness=0.05),
        row=2, col=1
    )

    return fig


def _calculate_drawdowns(values: List[float]) -> List[float]:
    """Calculate drawdown percentages from value series."""
    if not values:
        return []

    drawdowns = []
    peak = values[0]

    for value in values:
        if value > peak:
            peak = value
        drawdown = (value - peak) / peak if peak > 0 else 0
        drawdowns.append(drawdown)

    return drawdowns


def _create_empty_chart(message: str) -> go.Figure:
    """Create empty chart with message."""
    fig = go.Figure()

    fig.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        text=message,
        showarrow=False,
        font=dict(size=20, color='#9CA3AF'),
        xanchor='center',
        yanchor='middle'
    )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='#1F2937',
        paper_bgcolor='#1F2937',
        height=500,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig
