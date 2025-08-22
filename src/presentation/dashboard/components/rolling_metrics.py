# src/presentation/dashboard/components/rolling_metrics.py

import plotly.graph_objs as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any
import pandas as pd

from src.core.entities.portfolio import Portfolio


def create_rolling_metrics_chart(portfolio: Portfolio,
                                 rolling_metrics: Dict[str, Any],
                                 window_days: int = 365) -> go.Figure:
    """Create rolling metrics subplots."""

    # Get the appropriate window data
    window_key = f'{window_days}d'
    if window_key not in rolling_metrics:
        return _create_empty_metrics_chart(f"Not enough data for {window_days}-day window")

    window_data = rolling_metrics[window_key]

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            f'{window_days}-Day Rolling Sharpe Ratio',
            f'{window_days}-Day Rolling Sortino Ratio',
            f'{window_days}-Day Rolling Calmar Ratio',
            f'{window_days}-Day Rolling Win Rate'
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )

    # 1. Sharpe Ratio
    if window_data.get('sharpe'):
        dates = [item[0] for item in window_data['sharpe']]
        values = [item[1] for item in window_data['sharpe']]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name='Sharpe',
                line=dict(color='#3B82F6', width=2),
                hovertemplate='%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # Add benchmark lines
        fig.add_hline(y=1, line_dash="dash", line_color="#10B981",
                      annotation_text="Good (1.0)", row=1, col=1)
        fig.add_hline(y=0, line_dash="solid", line_color="#6B7280", row=1, col=1)

    # 2. Sortino Ratio
    if window_data.get('sortino'):
        dates = [item[0] for item in window_data['sortino']]
        values = [item[1] for item in window_data['sortino']]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name='Sortino',
                line=dict(color='#8B5CF6', width=2),
                hovertemplate='%{y:.2f}<extra></extra>'
            ),
            row=1, col=2
        )

        fig.add_hline(y=1.5, line_dash="dash", line_color="#10B981",
                      annotation_text="Good (1.5)", row=1, col=2)
        fig.add_hline(y=0, line_dash="solid", line_color="#6B7280", row=1, col=2)

    # 3. Calmar Ratio
    if window_data.get('calmar'):
        dates = [item[0] for item in window_data['calmar']]
        values = [item[1] for item in window_data['calmar']]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name='Calmar',
                line=dict(color='#10B981', width=2),
                hovertemplate='%{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )

        fig.add_hline(y=1, line_dash="dash", line_color="#10B981",
                      annotation_text="Good (1.0)", row=2, col=1)
        fig.add_hline(y=0, line_dash="solid", line_color="#6B7280", row=2, col=1)

    # 4. Win Rate
    if window_data.get('win_rate'):
        dates = [item[0] for item in window_data['win_rate']]
        values = [item[1] * 100 for item in window_data['win_rate']]  # Convert to percentage

        # Create filled area chart for win rate
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name='Win Rate',
                line=dict(color='#F59E0B', width=2),
                fill='tozeroy',
                fillcolor='rgba(245, 158, 11, 0.2)',
                hovertemplate='%{y:.1f}%<extra></extra>'
            ),
            row=2, col=2
        )

        # Add 50% line
        fig.add_hline(y=50, line_dash="dash", line_color="#6B7280",
                      annotation_text="50%", row=2, col=2)

        # Color regions
        fig.add_hrect(y0=50, y1=100, fillcolor="#10B981", opacity=0.1,
                      layer="below", line_width=0, row=2, col=2)
        fig.add_hrect(y0=0, y1=50, fillcolor="#EF4444", opacity=0.1,
                      layer="below", line_width=0, row=2, col=2)

    # Update layout
    fig.update_xaxes(
        gridcolor='#374151',
        showgrid=True,
        tickformat='%Y-%m'
    )

    fig.update_yaxes(
        gridcolor='#374151',
        showgrid=True
    )

    # Specific y-axis formatting
    fig.update_yaxes(title_text="Ratio", row=1, col=1)
    fig.update_yaxes(title_text="Ratio", row=1, col=2)
    fig.update_yaxes(title_text="Ratio", row=2, col=1)
    fig.update_yaxes(title_text="Win Rate (%)", row=2, col=2)

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='#1F2937',
        paper_bgcolor='#1F2937',
        font=dict(color='#F3F4F6'),
        showlegend=False,
        height=600,
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='x unified'
    )

    return fig


def _create_empty_metrics_chart(message: str) -> go.Figure:
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
        height=600,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig


def create_volatility_cone(portfolio: Portfolio,
                           rolling_metrics: Dict[str, Any]) -> go.Figure:
    """Create volatility cone chart showing percentiles over different periods."""

    # Calculate volatility percentiles for different rolling windows
    windows = [30, 60, 90, 180, 365]
    percentiles = [10, 25, 50, 75, 90]

    volatility_data = {}

    for window in windows:
        window_key = f'{window}d'
        if window_key in rolling_metrics and 'volatility' in rolling_metrics[window_key]:
            vols = [item[1] * 100 for item in rolling_metrics[window_key]['volatility']]
            if vols:
                volatility_data[window] = {
                    f'p{p}': pd.Series(vols).quantile(p / 100)
                    for p in percentiles
                }
                volatility_data[window]['current'] = vols[-1] if vols else 0

    if not volatility_data:
        return _create_empty_metrics_chart("Not enough data for volatility cone")

    fig = go.Figure()

    # Add percentile lines
    colors = {
        'p10': '#065F46',
        'p25': '#10B981',
        'p50': '#3B82F6',
        'p75': '#F59E0B',
        'p90': '#DC2626'
    }

    for percentile in ['p10', 'p25', 'p50', 'p75', 'p90']:
        x = list(volatility_data.keys())
        y = [volatility_data[w].get(percentile, 0) for w in x]

        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines+markers',
            name=f'{percentile[1:]}th percentile',
            line=dict(color=colors[percentile], width=2),
            marker=dict(size=8)
        ))

    # Add current volatility
    x = list(volatility_data.keys())
    y = [volatility_data[w].get('current', 0) for w in x]

    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines+markers',
        name='Current',
        line=dict(color='#FBBF24', width=3, dash='dash'),
        marker=dict(size=10, symbol='star')
    ))

    fig.update_layout(
        title="Volatility Cone - Rolling Window Analysis",
        xaxis_title="Rolling Window (Days)",
        yaxis_title="Annualized Volatility (%)",
        template="plotly_dark",
        plot_bgcolor='#1F2937',
        paper_bgcolor='#1F2937',
        font=dict(color='#F3F4F6'),
        height=500,
        hovermode='x unified'
    )

    return fig
