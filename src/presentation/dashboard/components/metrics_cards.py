# src/presentation/dashboard/components/metrics_cards.py

from dash import html
from typing import Dict, Any, Optional
from decimal import Decimal


def create_metric_card(
        title: str,
        value: Any,
        id_prefix: str,
        tooltip: Optional[str] = None,
        color: Optional[str] = None,
        format_type: str = "default"
) -> html.Div:
    """Create a single metric card component."""

    # Format value based on type
    formatted_value = format_metric_value(value, format_type)

    # Determine color based on value
    if color is None and isinstance(value, (int, float, Decimal)):
        if format_type in ["percent", "return"]:
            color = "#10B981" if value > 0 else "#EF4444" if value < 0 else "#9CA3AF"
        elif format_type == "ratio":
            if title.lower() == "sharpe ratio":
                color = "#10B981" if value > 1 else "#F59E0B" if value > 0 else "#EF4444"
            else:
                color = "#F3F4F6"
    else:
        color = color or "#F3F4F6"

    card_content = [
        html.Div([
            html.Span(title, style={
                'color': '#9CA3AF',
                'font-size': '0.875rem',
                'font-weight': '500'
            }),
        ], style={'margin-bottom': '8px'}),

        html.Div(
            id=f'{id_prefix}-value',
            children=formatted_value,
            style={
                'color': color,
                'font-size': '2rem',
                'font-weight': 'bold',
                'font-variant-numeric': 'tabular-nums'
            }
        )
    ]

    # Add tooltip if provided
    if tooltip:
        card_content[0].children.append(
            html.Span(
                "ⓘ",
                title=tooltip,
                style={
                    'color': '#6B7280',
                    'font-size': '0.75rem',
                    'margin-left': '5px',
                    'cursor': 'help'
                }
            )
        )

    return html.Div(
        card_content,
        style={
            'background-color': '#1F2937',
            'padding': '20px',
            'border-radius': '8px',
            'border': '1px solid #374151',
            'min-height': '100px',
            'display': 'flex',
            'flex-direction': 'column',
            'justify-content': 'center'
        }
    )


def format_metric_value(value: Any, format_type: str) -> str:
    """Format metric value based on type."""
    if value is None:
        return "N/A"

    try:
        if format_type == "percent":
            return f"{float(value):.2f}%"
        elif format_type == "return":
            sign = "+" if float(value) > 0 else ""
            return f"{sign}{float(value):.2f}%"
        elif format_type == "currency":
            return f"${float(value):,.2f}"
        elif format_type == "ratio":
            return f"{float(value):.2f}"
        elif format_type == "number":
            return f"{int(value):,}"
        else:
            return str(value)
    except:
        return str(value)


def create_metrics_grid(metrics: Dict[str, Any]) -> html.Div:
    """Create a grid of metric cards."""

    # Define metric configurations
    metric_configs = [
        ("Total Return", metrics.get('total_return_percent', 0), "total-return", "return",
         "Total profit/loss as percentage of invested capital"),

        ("CAGR", metrics.get('cagr', 0), "cagr", "percent",
         "Compound Annual Growth Rate"),

        ("Sharpe Ratio", metrics.get('sharpe_ratio', 0), "sharpe-ratio", "ratio",
         "Risk-adjusted returns (>1 is good, >2 is excellent)"),

        ("Sortino Ratio", metrics.get('sortino_ratio', 0), "sortino-ratio", "ratio",
         "Downside risk-adjusted returns"),

        ("Max Drawdown", metrics.get('max_drawdown', 0) * 100, "max-drawdown", "percent",
         "Largest peak-to-trough decline"),

        ("Win Rate", metrics.get('win_rate', 0) * 100, "win-rate", "percent",
         "Percentage of profitable trades"),

        ("Daily Volatility", metrics.get('daily_volatility', 0) * 100, "daily-volatility", "percent",
         "Average daily price movement"),

        ("Annual Volatility", metrics.get('annual_volatility', 0) * 100, "annual-volatility", "percent",
         "Annualized standard deviation"),

        ("Calmar Ratio", metrics.get('calmar_ratio', 0), "calmar-ratio", "ratio",
         "Annual return / Max drawdown"),

        ("Profit Factor", metrics.get('profit_factor', 0), "profit-factor", "ratio",
         "Total gains / Total losses")
    ]

    # Create cards
    cards = []
    for title, value, id_prefix, format_type, tooltip in metric_configs:
        cards.append(
            create_metric_card(title, value, id_prefix, tooltip, format_type=format_type)
        )

    # Create grid layout
    return html.Div([
        # First row - 6 columns
        html.Div(cards[:6], style={
            'display': 'grid',
            'grid-template-columns': 'repeat(6, 1fr)',
            'gap': '20px',
            'margin-bottom': '20px'
        }),

        # Second row - 4 columns
        html.Div(cards[6:], style={
            'display': 'grid',
            'grid-template-columns': 'repeat(4, 1fr)',
            'gap': '20px'
        })
    ])
