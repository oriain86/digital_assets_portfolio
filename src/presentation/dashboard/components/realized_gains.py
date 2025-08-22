# src/presentation/dashboard/components/realized_gains.py

from dash import html, dash_table, dcc
import plotly.graph_objs as go
from datetime import datetime
from typing import List, Dict, Any
from decimal import Decimal

from src.core.entities.portfolio import Portfolio


def create_realized_gains_section(portfolio: Portfolio) -> html.Div:
    """Create the realized gains history section."""

    # Calculate total realized P&L
    total_realized = Decimal('0')
    realized_trades = []

    # Collect all realized gains/losses
    for position in list(portfolio.positions.values()) + portfolio.closed_positions:
        for tx in position.transactions:
            if hasattr(tx, 'realized_gain_loss') and tx.realized_gain_loss is not None:
                realized_trades.append({
                    'date': tx.timestamp,
                    'symbol': tx.asset,
                    'amount': float(tx.amount),
                    'sale_price': float(tx.price_usd) if tx.price_usd else 0,
                    'cost_basis': float(tx.cost_basis) if hasattr(tx, 'cost_basis') else 0,
                    'realized_gain': float(tx.realized_gain_loss),
                    'type': 'Sell',
                    'exchange': tx.exchange or 'Unknown'
                })
                total_realized += tx.realized_gain_loss

    # Sort by date descending
    realized_trades.sort(key=lambda x: x['date'], reverse=True)

    # Format for display
    table_data = []
    for trade in realized_trades[:50]:  # Show last 50 trades
        table_data.append({
            'date': trade['date'].strftime('%Y-%m-%d'),
            'symbol': trade['symbol'],
            'amount': f"{trade['amount']:.6f}",
            'sale_price': f"${trade['sale_price']:,.2f}",
            'cost_basis': f"${trade['cost_basis']:,.2f}",
            'realized_gain': trade['realized_gain'],  # Keep as number for conditional formatting
            'exchange': trade['exchange']
        })

    return html.Div([
        # Header with total
        html.Div([
            html.H3(
                f"Total Realized Gains/Losses: ${float(total_realized):,.2f}",
                style={
                    'color': '#10B981' if total_realized >= 0 else '#EF4444',
                    'font-size': '1.25rem',
                    'margin-bottom': '20px',
                    'font-weight': 'bold'
                }
            ),

            # Summary statistics
            html.Div([
                _create_summary_stat("Total Trades", len(realized_trades)),
                _create_summary_stat("Winning Trades", len([t for t in realized_trades if t['realized_gain'] > 0])),
                _create_summary_stat("Losing Trades", len([t for t in realized_trades if t['realized_gain'] < 0])),
                _create_summary_stat("Win Rate",
                                     f"{len([t for t in realized_trades if t['realized_gain'] > 0]) / len(realized_trades) * 100:.1f}%" if realized_trades else "0%"),
            ], style={
                'display': 'grid',
                'grid-template-columns': 'repeat(4, 1fr)',
                'gap': '20px',
                'margin-bottom': '20px'
            })
        ]),

        # Expandable table
        html.Details([
            html.Summary("Show detailed realized gains", style={
                'color': '#9CA3AF',
                'cursor': 'pointer',
                'padding': '10px',
                'background-color': '#111827',
                'border-radius': '4px',
                'margin-bottom': '10px',
                'user-select': 'none'
            }),

            # Table
            dash_table.DataTable(
                id='realized-gains-table',
                columns=[
                    {'name': 'Date', 'id': 'date'},
                    {'name': 'Symbol', 'id': 'symbol'},
                    {'name': 'Amount', 'id': 'amount'},
                    {'name': 'Sale Price', 'id': 'sale_price'},
                    {'name': 'Cost Basis', 'id': 'cost_basis'},
                    {'name': 'Realized Gain', 'id': 'realized_gain', 'type': 'numeric',
                     'format': {'specifier': '$,.2f'}},
                    {'name': 'Exchange', 'id': 'exchange'}
                ],
                data=table_data,
                style_cell={
                    'textAlign': 'left',
                    'backgroundColor': '#1F2937',
                    'color': 'white',
                    'border': '1px solid #374151',
                    'font-family': 'monospace',
                    'fontSize': '0.9rem',
                    'padding': '8px'
                },
                style_header={
                    'backgroundColor': '#111827',
                    'fontWeight': 'bold',
                    'border': '1px solid #374151'
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'realized_gain', 'filter_query': '{realized_gain} > 0'},
                        'color': '#10B981'
                    },
                    {
                        'if': {'column_id': 'realized_gain', 'filter_query': '{realized_gain} < 0'},
                        'color': '#EF4444'
                    },
                    {
                        'if': {'state': 'selected'},
                        'backgroundColor': '#374151',
                        'border': '1px solid #374151'
                    }
                ],
                page_size=20,
                sort_action='native',
                filter_action='native',
                style_table={
                    'overflowX': 'auto'
                },
                style_filter={
                    'backgroundColor': '#374151',
                    'color': 'white'
                }
            ),

            # Monthly summary chart
            create_monthly_realized_chart(realized_trades)
        ], open=False)  # Start collapsed
    ], style={
        'background-color': '#1F2937',
        'border-radius': '8px',
        'padding': '20px',
        'border': '1px solid #374151'
    })


def _create_summary_stat(label: str, value: Any) -> html.Div:
    """Create a summary statistic card."""
    return html.Div([
        html.P(label, style={
            'color': '#9CA3AF',
            'font-size': '0.875rem',
            'margin-bottom': '4px'
        }),
        html.P(str(value), style={
            'color': 'white',
            'font-size': '1.25rem',
            'font-weight': 'bold'
        })
    ], style={
        'text-align': 'center',
        'padding': '10px',
        'background-color': '#111827',
        'border-radius': '4px'
    })


def create_monthly_realized_chart(realized_trades: List[Dict[str, Any]]) -> html.Div:
    """Create monthly realized gains/losses chart."""
    if not realized_trades:
        return html.Div()

    # Group by month
    monthly_data = {}
    for trade in realized_trades:
        month_key = trade['date'].strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'gains': 0, 'losses': 0}

        if trade['realized_gain'] > 0:
            monthly_data[month_key]['gains'] += trade['realized_gain']
        else:
            monthly_data[month_key]['losses'] += abs(trade['realized_gain'])

    # Sort by month
    sorted_months = sorted(monthly_data.keys())

    # Prepare data for chart
    months = []
    gains = []
    losses = []
    net = []

    for month in sorted_months:
        months.append(month)
        gains.append(monthly_data[month]['gains'])
        losses.append(-monthly_data[month]['losses'])  # Negative for display
        net.append(monthly_data[month]['gains'] - monthly_data[month]['losses'])

    # Create figure
    fig = go.Figure()

    # Add gains bars
    fig.add_trace(go.Bar(
        x=months,
        y=gains,
        name='Gains',
        marker_color='#10B981',
        text=[f"${g:,.0f}" for g in gains],
        textposition='auto',
        hovertemplate='%{x}<br>Gains: $%{y:,.2f}<extra></extra>'
    ))

    # Add losses bars
    fig.add_trace(go.Bar(
        x=months,
        y=losses,
        name='Losses',
        marker_color='#EF4444',
        text=[f"${abs(l):,.0f}" for l in losses],
        textposition='auto',
        hovertemplate='%{x}<br>Losses: $%{y:,.2f}<extra></extra>'
    ))

    # Add net line
    fig.add_trace(go.Scatter(
        x=months,
        y=net,
        name='Net',
        mode='lines+markers',
        line=dict(color='#F59E0B', width=3),
        marker=dict(size=8),
        yaxis='y2',
        hovertemplate='%{x}<br>Net: $%{y:,.2f}<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        title="Monthly Realized Gains/Losses",
        template="plotly_dark",
        plot_bgcolor='#1F2937',
        paper_bgcolor='#1F2937',
        font=dict(color='#F3F4F6'),
        barmode='relative',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        yaxis=dict(
            title="Gains/Losses ($)",
            gridcolor='#374151',
            zeroline=True,
            zerolinecolor='#6B7280'
        ),
        yaxis2=dict(
            title="Net ($)",
            overlaying='y',
            side='right',
            gridcolor='#374151',
            zeroline=True,
            zerolinecolor='#6B7280'
        ),
        xaxis=dict(
            title="Month",
            gridcolor='#374151'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )

    return html.Div([
        html.H4("Monthly Realized P&L Trend", style={
            'color': 'white',
            'font-size': '1rem',
            'margin': '20px 0 10px 0'
        }),
        dcc.Graph(
            figure=fig,
            config={'displayModeBar': False}
        )
    ])
