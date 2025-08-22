# src/presentation/dashboard/components/positions_table.py

from dash import html, dash_table, dcc
import plotly.graph_objs as go
from typing import List, Dict, Any
import pandas as pd

from src.core.entities.portfolio import Portfolio


def create_positions_table_section(portfolio: Portfolio) -> html.Div:
    """Create the current positions table with enhanced features."""

    # Prepare positions data
    positions_data = []
    total_value = portfolio.get_total_value()

    for asset, position in portfolio.positions.items():
        if position.current_amount > 0 and asset != portfolio.base_currency:
            current_value = position.get_current_value()
            unrealized_pnl = position.get_unrealized_pnl()
            unrealized_pct = position.get_unrealized_pnl_percent()

            positions_data.append({
                'symbol': asset,
                'amount': float(position.current_amount),
                'avg_cost': float(position.get_average_cost()),
                'current_price': float(position.current_price) if position.current_price else 0,
                'total_cost': float(position.total_cost_basis),
                'current_value': float(current_value),
                'unrealized_pnl': float(unrealized_pnl),
                'unrealized_pct': float(unrealized_pct),
                'allocation': float(current_value / total_value * 100) if total_value > 0 else 0,
                'transactions': len(position.transactions),
                'holding_days': position.get_holding_period_days()
            })

    # Sort by current value descending
    positions_data.sort(key=lambda x: x['current_value'], reverse=True)

    # Calculate totals
    total_cost = sum(p['total_cost'] for p in positions_data)
    total_current_value = sum(p['current_value'] for p in positions_data)
    total_unrealized_pnl = sum(p['unrealized_pnl'] for p in positions_data)
    total_unrealized_pct = (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0

    return html.Div([
        # Header with summary
        html.Div([
            html.H2([
                "📋 Current Positions"
            ], style={
                'color': 'white',
                'font-size': '1.5rem',
                'margin-bottom': '20px',
                'font-weight': '600'
            }),

            # Summary cards
            html.Div([
                _create_position_summary_card("Total Positions", len(positions_data), "📊"),
                _create_position_summary_card("Total Value", f"${total_current_value:,.2f}", "💰"),
                _create_position_summary_card("Total Cost", f"${total_cost:,.2f}", "💵"),
                _create_position_summary_card(
                    "Unrealized P&L",
                    f"${total_unrealized_pnl:,.2f} ({total_unrealized_pct:+.1f}%)",
                    "📈" if total_unrealized_pnl >= 0 else "📉",
                    color='#10B981' if total_unrealized_pnl >= 0 else '#EF4444'
                ),
            ], style={
                'display': 'grid',
                'grid-template-columns': 'repeat(4, 1fr)',
                'gap': '15px',
                'margin-bottom': '20px'
            })
        ]),

        # Table with enhanced features
        html.Div([
            # Table controls
            html.Div([
                html.Div([
                    html.Label("Show: ", style={'color': '#9CA3AF', 'margin-right': '10px'}),
                    dcc.Dropdown(
                        id='positions-display-filter',
                        options=[
                            {'label': 'All Positions', 'value': 'all'},
                            {'label': 'Gainers Only', 'value': 'gainers'},
                            {'label': 'Losers Only', 'value': 'losers'},
                            {'label': 'Top 10 by Value', 'value': 'top10'}
                        ],
                        value='all',
                        style={'width': '200px', 'display': 'inline-block'}
                    )
                ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '15px'})
            ]),

            # Main table
            dash_table.DataTable(
                id='positions-table',
                columns=[
                    {'name': '#', 'id': 'index', 'type': 'numeric'},
                    {'name': 'Symbol', 'id': 'symbol'},
                    {'name': 'Amount', 'id': 'amount', 'type': 'numeric', 'format': {'specifier': ',.4f'}},
                    {'name': 'Avg Cost', 'id': 'avg_cost', 'type': 'numeric', 'format': {'specifier': '$,.2f'}},
                    {'name': 'Current Price', 'id': 'current_price', 'type': 'numeric',
                     'format': {'specifier': '$,.2f'}},
                    {'name': 'Total Cost', 'id': 'total_cost', 'type': 'numeric', 'format': {'specifier': '$,.2f'}},
                    {'name': 'Current Value', 'id': 'current_value', 'type': 'numeric',
                     'format': {'specifier': '$,.2f'}},
                    {'name': 'Unrealized P&L', 'id': 'unrealized_pnl', 'type': 'numeric',
                     'format': {'specifier': '$,.2f'}},
                    {'name': 'Unrealized %', 'id': 'unrealized_pct', 'type': 'numeric',
                     'format': {'specifier': ',.2f%'}},
                    {'name': 'Allocation %', 'id': 'allocation', 'type': 'numeric', 'format': {'specifier': ',.1f%'}},
                    {'name': 'Days Held', 'id': 'holding_days', 'type': 'numeric'}
                ],
                data=[{**p, 'index': i + 1} for i, p in enumerate(positions_data)],
                style_cell={
                    'textAlign': 'left',
                    'backgroundColor': '#1F2937',
                    'color': 'white',
                    'border': '1px solid #374151',
                    'font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace',
                    'fontSize': '0.9rem',
                    'padding': '10px'
                },
                style_header={
                    'backgroundColor': '#111827',
                    'fontWeight': 'bold',
                    'border': '1px solid #374151',
                    'position': 'sticky',
                    'top': 0
                },
                style_data_conditional=[
                    # Color coding for P&L
                    {
                        'if': {'column_id': 'unrealized_pnl', 'filter_query': '{unrealized_pnl} > 0'},
                        'color': '#10B981'
                    },
                    {
                        'if': {'column_id': 'unrealized_pnl', 'filter_query': '{unrealized_pnl} < 0'},
                        'color': '#EF4444'
                    },
                    {
                        'if': {'column_id': 'unrealized_pct', 'filter_query': '{unrealized_pct} > 0'},
                        'color': '#10B981'
                    },
                    {
                        'if': {'column_id': 'unrealized_pct', 'filter_query': '{unrealized_pct} < 0'},
                        'color': '#EF4444'
                    },
                    # Highlight large positions
                    {
                        'if': {'column_id': 'allocation', 'filter_query': '{allocation} > 20'},
                        'backgroundColor': '#7C3AED',
                        'color': 'white'
                    },
                    # Row hover effect
                    {
                        'if': {'state': 'selected'},
                        'backgroundColor': '#374151',
                        'border': '1px solid #4B5563'
                    },
                    # Make index column smaller
                    {
                        'if': {'column_id': 'index'},
                        'width': '5%',
                        'textAlign': 'center',
                        'color': '#6B7280'
                    },
                    # Symbol column styling
                    {
                        'if': {'column_id': 'symbol'},
                        'fontWeight': 'bold',
                        'color': '#60A5FA'
                    }
                ],
                sort_action='native',
                filter_action='native',
                page_action='none',  # Show all rows
                style_table={
                    'overflowX': 'auto',
                    'maxHeight': '600px',
                    'overflowY': 'auto'
                },
                style_filter={
                    'backgroundColor': '#374151',
                    'color': 'white'
                },
                export_format='csv',
                export_headers='display',
                merge_duplicate_headers=True
            )
        ], style={
            'background-color': '#1F2937',
            'border-radius': '8px',
            'padding': '20px',
            'border': '1px solid #374151'
        }),

        # Allocation pie chart
        create_allocation_chart(positions_data)

    ], style={'margin-bottom': '40px'})


def _create_position_summary_card(title: str, value: str, emoji: str, color: str = 'white') -> html.Div:
    """Create a summary card for positions section."""
    return html.Div([
        html.Div([
            html.Span(emoji, style={'font-size': '1.5rem', 'margin-right': '8px'}),
            html.Span(title, style={'color': '#9CA3AF', 'font-size': '0.875rem'})
        ]),
        html.Div(value, style={
            'color': color,
            'font-size': '1.25rem',
            'font-weight': 'bold',
            'margin-top': '4px'
        })
    ], style={
        'background-color': '#111827',
        'padding': '15px',
        'border-radius': '6px',
        'border': '1px solid #374151'
    })


def create_allocation_chart(positions_data: List[Dict[str, Any]]) -> html.Div:
    """Create allocation pie chart."""
    if not positions_data:
        return html.Div()

    # Prepare data for pie chart
    labels = []
    values = []
    colors = []

    # Get top 10 positions
    top_positions = sorted(positions_data, key=lambda x: x['allocation'], reverse=True)[:10]
    other_allocation = sum(p['allocation'] for p in positions_data[10:])

    # Color palette
    color_scale = [
        '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
        '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16'
    ]

    for i, pos in enumerate(top_positions):
        labels.append(pos['symbol'])
        values.append(pos['allocation'])
        colors.append(color_scale[i % len(color_scale)])

    if other_allocation > 0:
        labels.append('Others')
        values.append(other_allocation)
        colors.append('#6B7280')

    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors, line=dict(color='#1F2937', width=2)),
        textfont=dict(color='white'),
        textposition='outside',
        textinfo='label+percent',
        hovertemplate='%{label}<br>Allocation: %{value:.1f}%<br>%{percent}<extra></extra>'
    )])

    # Update layout
    fig.update_layout(
        title="Portfolio Allocation",
        template="plotly_dark",
        plot_bgcolor='#1F2937',
        paper_bgcolor='#1F2937',
        font=dict(color='#F3F4F6'),
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )

    # Add center text
    fig.add_annotation(
        text=f"{len(positions_data)}<br>Assets",
        x=0.5, y=0.5,
        font=dict(size=20, color='white'),
        showarrow=False
    )

    return html.Div([
        dcc.Graph(
            figure=fig,
            config={'displayModeBar': False}
        )
    ], style={
        'background-color': '#1F2937',
        'border-radius': '8px',
        'padding': '20px',
        'border': '1px solid #374151',
        'margin-top': '20px'
    })
