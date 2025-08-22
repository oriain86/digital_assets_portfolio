
from dash import html, dcc


def create_base_layout(content):
    """Create base layout wrapper for all pages."""
    return html.Div([
        # Header
        html.Header([
            html.Div([
                html.H1([
                    html.Span("🚀 ", style={'margin-right': '10px'}),
                    "Crypto Portfolio Tracker"
                ], style={
                    'color': 'white',
                    'margin': '0',
                    'font-size': '2rem',
                    'font-weight': 'bold'
                }),
            ], style={
                'padding': '20px',
                'background-color': '#1F2937',
                'border-bottom': '1px solid #374151'
            })
        ]),

        # Main content
        html.Main([
            content
        ], style={
            'min-height': 'calc(100vh - 80px)',
            'background-color': '#111827',
            'padding': '20px'
        }),

        # Footer
        html.Footer([
            html.P("© 2024 Crypto Portfolio Tracker", style={
                'text-align': 'center',
                'color': '#6B7280',
                'padding': '20px'
            })
        ], style={
            'background-color': '#1F2937',
            'border-top': '1px solid #374151'
        })
    ], style={
        'min-height': '100vh',
        'background-color': '#111827'
    })
