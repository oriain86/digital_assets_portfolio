
from dash import html, dcc
from src.presentation.dashboard.layouts.base_layout import create_base_layout


def create_main_layout():
    """Create main dashboard layout."""
    content = html.Div([
        # Navigation tabs
        dcc.Tabs(id='main-tabs', value='portfolio', children=[
            dcc.Tab(label='📊 Portfolio', value='portfolio'),
            dcc.Tab(label='📈 Analytics', value='analytics'),
            dcc.Tab(label='💰 Positions', value='positions'),
            dcc.Tab(label='📋 Transactions', value='transactions'),
            dcc.Tab(label='📑 Reports', value='reports'),
        ], style={
            'backgroundColor': '#1F2937',
            'borderBottom': '1px solid #374151'
        }),

        # Tab content
        html.Div(id='tab-content', style={'padding': '20px'})
    ])

    return create_base_layout(content)
