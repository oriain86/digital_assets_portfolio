# src/presentation/dashboard/app.py

from decimal import Decimal
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from typing import Dict, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DashboardApp:
    """Dashboard for portfolio visualization with professional metrics."""

    def __init__(self, portfolio_service):
        self.portfolio_service = portfolio_service
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        """Create the dashboard layout."""
        self.app.layout = html.Div([
            html.H1("🚀 Crypto Portfolio Dashboard",
                    style={'textAlign': 'center', 'color': '#1f77b4', 'marginBottom': '30px'}),

            # Metrics cards - Two rows of metrics
            html.Div(id='metrics-cards', style={'margin': '20px'}),

            # Summary section with insights
            html.Div(id='portfolio-summary', style={'margin': '20px'}),

            # Main charts row - portfolio value chart and monthly returns
            html.Div([
                html.Div([
                    dcc.Graph(id='portfolio-value-chart', style={'height': '500px'}),
                ], style={'width': '65%', 'display': 'inline-block', 'padding': '10px'}),

                html.Div([
                    dcc.Graph(id='monthly-returns-chart', style={'height': '500px'}),
                ], style={'width': '35%', 'display': 'inline-block', 'padding': '10px'}),
            ], style={'display': 'flex'}),

            # Auto-refresh
            dcc.Interval(
                id='interval-component',
                interval=60 * 1000,  # Update every minute
                n_intervals=0
            )
        ])

    def setup_callbacks(self):
        """Setup dashboard callbacks."""

        @self.app.callback(
            [
                Output('metrics-cards', 'children'),
                Output('portfolio-summary', 'children'),
                Output('portfolio-value-chart', 'figure'),
                Output('monthly-returns-chart', 'figure'),
            ],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            try:
                # Get fresh metrics using the new structure
                from src.application.use_cases.calculate_metrics import CalculateMetricsUseCase

                calc_metrics_use_case = CalculateMetricsUseCase()

                # Get metrics for the fixed date range (Jul 1, 2023 - Feb 23, 2025)
                metrics_result = calc_metrics_use_case.execute(
                    self.portfolio_service.portfolio,
                    {'include_monthly_breakdown': True}
                )

                if not metrics_result['success']:
                    raise Exception(metrics_result.get('error', 'Failed to calculate metrics'))

                # Create components
                metrics_cards = self._create_metrics_cards(metrics_result)
                summary_section = self._create_summary_section(metrics_result)
                portfolio_fig = self._create_portfolio_value_figure(metrics_result)
                monthly_returns_fig = self._create_monthly_returns_chart(metrics_result)

                return (
                    metrics_cards,
                    summary_section,
                    portfolio_fig,
                    monthly_returns_fig,
                )
            except Exception as e:
                logger.error(f"Error updating dashboard: {e}")
                empty_fig = go.Figure()
                return [], [], empty_fig, empty_fig

    def _create_metrics_cards(self, metrics_result: Dict[str, Any]):
        """Create metric display cards with date range label."""
        cards = []

        performance = metrics_result.get('performance', {})
        risk = metrics_result.get('risk', {})
        trading = metrics_result.get('trading', {})

        # Extract date range for label (Jul 1 '23 - Feb 23 '25)
        date_label = "Jul 1 '23 - Feb 23 '25"

        # First row of metrics
        first_row_metrics = [
            (f"💰 Total Return ({date_label})", f"${performance.get('total_return', 0):,.2f}",
             f"{performance.get('total_return_pct', 0):.1f}%",
             'green' if performance.get('total_return', 0) > 0 else 'red'),
            (f"💵 Net Profit ({date_label})", f"${performance.get('net_profit', 0):,.2f}",
             "After all fees",
             'green' if performance.get('net_profit', 0) > 0 else 'red'),
            (f"📈 Annual Return ({date_label})", f"{performance.get('annualized_return', 0):.1f}%", None,
             'green' if performance.get('annualized_return', 0) > 0 else 'red'),
            (f"📐 Sharpe Ratio ({date_label})", f"{risk.get('sharpe_ratio', 0):.2f}", None, '#1f77b4'),
            (f"📉 Max Drawdown ({date_label})", f"{risk.get('max_drawdown', 0):.1f}%", None, 'red'),
        ]

        # Calculate fee impact correctly
        total_fees = metrics_result.get('performance', {}).get('total_fees', 0)
        net_invested = performance.get('net_invested', 1)  # Avoid division by zero
        fee_percentage = (total_fees / net_invested * 100) if net_invested > 0 else 0

        # Second row of metrics
        second_row_metrics = [
            (f"🎯 Win Rate ({date_label})", f"{trading.get('win_rate', 0):.1f}%", None,
             'green' if trading.get('win_rate', 0) > 50 else 'red'),
            (f"💹 Total Trades ({date_label})", f"{trading.get('total_trades', 0)}", None, '#1f77b4'),
            (f"📊 Sortino Ratio ({date_label})", f"{risk.get('sortino_ratio', 0):.2f}", None, '#1f77b4'),
            (f"📈 Beta vs BTC ({date_label})", f"{risk.get('beta', 0):.2f}", None, '#1f77b4'),
            (f"💸 Total Fees ({date_label})",
             f"${total_fees:,.2f}",
             f"{fee_percentage:.1f}% of invested",
             'orange'),
        ]

        # Create first row
        first_row = html.Div([
            self._create_metric_card(title, value, subtitle, color)
            for title, value, subtitle, color in first_row_metrics
        ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '10px'})

        # Create second row
        second_row = html.Div([
            self._create_metric_card(title, value, subtitle, color)
            for title, value, subtitle, color in second_row_metrics
        ], style={'display': 'flex', 'justifyContent': 'space-around'})

        return [first_row, second_row]

    def _create_metric_card(self, title, value, subtitle, color):
        """Create individual metric card."""
        return html.Div([
            html.H5(title, style={'margin': '5px', 'color': '#666', 'fontSize': '14px'}),
            html.H3(value, style={'margin': '5px', 'color': color}),
            html.P(subtitle, style={'margin': '2px', 'fontSize': '12px', 'color': '#999'}) if subtitle else None
        ], style={
            'border': '1px solid #ddd',
            'borderRadius': '8px',
            'padding': '15px',
            'margin': '5px',
            'width': '180px',
            'textAlign': 'center',
            'backgroundColor': '#f9f9f9',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        })

    def _create_portfolio_value_figure(self, metrics: Dict[str, Any]):
        """Create portfolio value chart showing data from Jul 1, 2023 to Feb 23, 2025."""
        fig = go.Figure()

        time_series = metrics.get('time_series', {})

        if time_series and 'dates' in time_series and 'values' in time_series:
            dates = time_series['dates']
            values = time_series['values']

            # Filter data to only show Jul 1, 2023 to Feb 23, 2025
            from datetime import datetime
            start_date = datetime(2023, 7, 1).date()
            end_date = datetime(2025, 2, 23).date()

            # Convert dates to comparable format and filter
            filtered_dates = []
            filtered_values = []

            for date, value in zip(dates, values):
                # Convert date to date object if it's datetime
                if hasattr(date, 'date'):
                    date_obj = date.date()
                else:
                    date_obj = date

                if start_date <= date_obj <= end_date:
                    filtered_dates.append(date)
                    filtered_values.append(value)

            # Use filtered data for the chart
            fig.add_trace(go.Scatter(
                x=filtered_dates,
                y=filtered_values,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.1)'
            ))

            fig.update_layout(
                title={
                    'text': 'Portfolio Value Over Time (Jul 1, 2023 - Feb 23, 2025)',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=20)
                },
                xaxis_title='Date',
                yaxis_title='Value (USD)',
                hovermode='x',
                height=500,
                template='plotly_white',
                yaxis=dict(
                    tickformat='$,.0f',
                    rangemode='tozero'  # Ensure y-axis starts from 0
                ),
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray',
                    range=[start_date, end_date]  # Set x-axis range explicitly
                ),
                showlegend=False
            )

            # Add annotation for current value
            if filtered_values and filtered_dates:
                current_value = filtered_values[-1]
                current_date = filtered_dates[-1]

                # Add annotation for final value
                fig.add_annotation(
                    x=current_date,
                    y=current_value,
                    text=f"${current_value:,.0f}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor="#1f77b4",
                    ax=-50,
                    ay=-30,
                    font=dict(size=14, color='#1f77b4')
                )
        else:
            fig.add_annotation(
                text="No time series data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )

        return fig

    def _create_summary_section(self, metrics_result: Dict[str, Any]):
        """Create portfolio summary section with insights and ratings."""
        summary = metrics_result.get('summary', {})

        # Extract key information
        health_score = summary.get('health_score', 0)
        risk_level = summary.get('risk_level', 'Unknown')
        performance_rating = summary.get('performance_rating', 'Unknown')
        insights = summary.get('key_insights', [])

        # Determine colors for ratings
        health_color = 'green' if health_score >= 70 else 'orange' if health_score >= 40 else 'red'
        risk_color = 'green' if risk_level == 'Low' else 'orange' if risk_level == 'Medium' else 'red'
        perf_color = 'green' if performance_rating in ['Excellent',
                                                       'Good'] else 'orange' if performance_rating == 'Average' else 'red'

        # Create summary cards
        summary_cards = html.Div([
            # Health Score Card
            html.Div([
                html.H4("Portfolio Health Score", style={'margin': '10px', 'color': '#666'}),
                html.Div([
                    html.H1(f"{health_score:.0f}/100", style={'margin': '10px', 'color': health_color}),
                    html.P("Overall portfolio health based on returns, risk, and consistency",
                           style={'margin': '10px', 'fontSize': '12px', 'color': '#999'})
                ])
            ], style={
                'border': '2px solid #ddd',
                'borderRadius': '10px',
                'padding': '20px',
                'margin': '10px',
                'width': '300px',
                'textAlign': 'center',
                'backgroundColor': '#f9f9f9',
                'display': 'inline-block'
            }),

            # Risk Level Card
            html.Div([
                html.H4("Risk Assessment", style={'margin': '10px', 'color': '#666'}),
                html.Div([
                    html.H2(risk_level, style={'margin': '10px', 'color': risk_color}),
                    html.P("Based on drawdown, volatility, and beta",
                           style={'margin': '10px', 'fontSize': '12px', 'color': '#999'})
                ])
            ], style={
                'border': '2px solid #ddd',
                'borderRadius': '10px',
                'padding': '20px',
                'margin': '10px',
                'width': '300px',
                'textAlign': 'center',
                'backgroundColor': '#f9f9f9',
                'display': 'inline-block'
            }),

            # Performance Rating Card
            html.Div([
                html.H4("Performance Rating", style={'margin': '10px', 'color': '#666'}),
                html.Div([
                    html.H2(performance_rating, style={'margin': '10px', 'color': perf_color}),
                    html.P("Overall performance assessment",
                           style={'margin': '10px', 'fontSize': '12px', 'color': '#999'})
                ])
            ], style={
                'border': '2px solid #ddd',
                'borderRadius': '10px',
                'padding': '20px',
                'margin': '10px',
                'width': '300px',
                'textAlign': 'center',
                'backgroundColor': '#f9f9f9',
                'display': 'inline-block'
            }),
        ], style={'textAlign': 'center', 'marginBottom': '20px'})

        # Create insights section
        insights_section = html.Div([
            html.H3("Key Insights", style={'color': '#1f77b4', 'marginBottom': '15px'}),
            html.Ul([
                html.Li(insight, style={'marginBottom': '10px', 'fontSize': '14px'})
                for insight in insights
            ])
        ], style={
            'backgroundColor': '#f0f8ff',
            'borderRadius': '10px',
            'padding': '20px',
            'margin': '20px 0'
        })

        return html.Div([summary_cards, insights_section])

    def _create_monthly_returns_chart(self, metrics_result: Dict[str, Any]):
        """Create monthly returns bar chart."""
        fig = go.Figure()

        monthly_returns = metrics_result.get('monthly_returns', [])

        if monthly_returns:
            months = [item['month'] for item in monthly_returns]
            returns = [item['return'] for item in monthly_returns]

            # Create colors based on positive/negative returns
            colors = ['green' if r > 0 else 'red' for r in returns]

            fig.add_trace(go.Bar(
                x=months,
                y=returns,
                marker_color=colors,
                text=[f"{r:.1f}%" for r in returns],
                textposition='outside',
                name='Monthly Returns'
            ))

            fig.update_layout(
                title={
                    'text': 'Monthly Returns (%)',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                xaxis_title='Month',
                yaxis_title='Return (%)',
                height=500,
                template='plotly_white',
                showlegend=False,
                yaxis=dict(
                    tickformat='.1f',
                    zeroline=True,
                    zerolinewidth=2,
                    zerolinecolor='black'
                ),
                xaxis=dict(
                    tickangle=-45
                )
            )

            # Add average line
            if returns:
                avg_return = sum(returns) / len(returns)
                fig.add_hline(
                    y=avg_return,
                    line_dash="dash",
                    line_color="blue",
                    annotation_text=f"Avg: {avg_return:.1f}%",
                    annotation_position="right"
                )
        else:
            fig.add_annotation(
                text="No monthly returns data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )

        return fig

    def run(self, debug=False, host='127.0.0.1', port=8050):
        """Run the dashboard."""
        self.app.run(debug=debug, host=host, port=port)
