# src/presentation/cli/commands.py

import click
import json
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

from src.application.services.portfolio_service import PortfolioService
from src.application.services.metrics_calculator import MetricsCalculator
from config.settings import settings
from config.logging import setup_logging


@click.group()
@click.pass_context
def cli(ctx):
    """Crypto Portfolio Tracker CLI"""
    setup_logging(log_to_console=True, log_to_file=False)
    ctx.obj = PortfolioService()


@cli.command()
@click.option('--csv', '-c', required=True, help='Path to CSV file')
@click.option('--method', '-m', default='FIFO',
              type=click.Choice(['FIFO', 'LIFO', 'HIFO']),
              help='Cost basis method')
@click.pass_obj
def init(portfolio_service, csv, method):
    """Initialize portfolio from CSV file"""
    click.echo(f"Initializing portfolio from {csv}...")

    portfolio_service.cost_basis_method = method
    result = portfolio_service.initialize_portfolio(csv)

    if result['success']:
        summary = result['summary']
        click.secho("✓ Portfolio initialized successfully!", fg='green')
        click.echo(f"  Transactions: {summary['total_transactions']}")
        click.echo(f"  Positions: {summary['current_positions']}")
        click.echo(f"  Total Value: ${summary['total_value']:,.2f}")
        click.echo(f"  Net Invested: ${summary['net_invested']:,.2f}")
    else:
        click.secho(f"✗ Error: {result['error']}", fg='red')


@cli.command()
@click.pass_obj
def status(portfolio_service):
    """Show portfolio status"""
    if not portfolio_service.load_portfolio():
        click.secho("No portfolio found. Run 'init' first.", fg='yellow')
        return

    portfolio = portfolio_service.get_portfolio()
    metrics = portfolio_service.get_portfolio_metrics()

    click.echo("\n📊 Portfolio Status")
    click.echo("=" * 50)

    # Basic info
    basic_metrics = metrics.get('basic', {})
    click.echo(f"Total Value: ${portfolio.get_total_value():,.2f}")
    click.echo(f"Net Invested: ${portfolio.total_deposits - portfolio.total_withdrawals:,.2f}")
    click.echo(f"Total Return: ${basic_metrics.get('total_return', 0):,.2f} "
               f"({basic_metrics.get('total_return_percent', 0):.2f}%)")

    # Performance metrics
    click.echo("\n📈 Performance Metrics")
    click.echo("-" * 30)
    click.echo(f"Sharpe Ratio: {basic_metrics.get('sharpe_ratio', 0):.2f}")
    click.echo(f"Max Drawdown: {basic_metrics.get('max_drawdown', 0) * 100:.2f}%")
    click.echo(f"Win Rate: {basic_metrics.get('win_rate', 0) * 100:.2f}%")

    # Current positions
    click.echo("\n💰 Current Positions")
    click.echo("-" * 30)

    positions_data = []
    for asset, position in portfolio.positions.items():
        if position.current_amount > 0 and asset != 'USD':
            positions_data.append([
                asset,
                f"{position.current_amount:.4f}",
                f"${position.get_average_cost():.2f}",
                f"${position.current_price:.2f}" if position.current_price else "N/A",
                f"${position.get_current_value():.2f}",
                f"{position.get_unrealized_pnl_percent():.2f}%"
            ])

    if positions_data:
        headers = ["Asset", "Amount", "Avg Cost", "Price", "Value", "P&L %"]
        click.echo(tabulate(positions_data, headers=headers, tablefmt="simple"))


@cli.command()
@click.pass_obj
def update(portfolio_service):
    """Update portfolio prices"""
    if not portfolio_service.load_portfolio():
        click.secho("No portfolio found. Run 'init' first.", fg='yellow')
        return

    click.echo("Updating prices...")
    result = portfolio_service.update_portfolio()

    if result['success']:
        click.secho("✓ Prices updated successfully!", fg='green')
        click.echo(f"  Total Value: ${result['total_value']:,.2f}")
    else:
        click.secho(f"✗ Error: {result['error']}", fg='red')


@cli.command()
@click.argument('asset')
@click.pass_obj
def position(portfolio_service, asset):
    """Show detailed position information"""
    if not portfolio_service.load_portfolio():
        click.secho("No portfolio found. Run 'init' first.", fg='yellow')
        return

    details = portfolio_service.get_position_details(asset.upper())

    if not details:
        click.secho(f"Position not found: {asset}", fg='red')
        return

    click.echo(f"\n📊 Position Details: {asset.upper()}")
    click.echo("=" * 50)

    # Basic info
    click.echo(f"Current Amount: {details['current_amount']:.8f}")
    click.echo(f"Average Cost: ${details['average_cost']:.2f}")
    click.echo(f"Current Price: ${details['current_price']:.2f}" if details['current_price'] else "Current Price: N/A")
    click.echo(f"Total Cost: ${details['total_cost_basis']:.2f}")
    click.echo(f"Current Value: ${details['current_value']:.2f}")

    # P&L
    click.echo("\n💰 Profit/Loss")
    click.echo("-" * 30)
    click.echo(f"Unrealized P&L: ${details['unrealized_pnl']:.2f} ({details['unrealized_pnl_percent']:.2f}%)")
    click.echo(f"Realized Gains: ${details['realized_gains']:.2f}")
    click.echo(f"Realized Losses: ${details['realized_losses']:.2f}")
    click.echo(f"Total Realized: ${details['total_realized_pnl']:.2f}")

    # Cost basis lots
    if details.get('cost_basis_lots'):
        click.echo("\n📦 Cost Basis Lots")
        click.echo("-" * 30)

        lot_data = []
        for lot in details['cost_basis_lots'][:10]:  # Show first 10
            lot_data.append([
                lot['acquisition_date'][:10],
                f"{lot['amount']:.8f}",
                f"${lot['cost_per_unit']:.2f}",
                f"${lot['total_cost']:.2f}"
            ])

        headers = ["Date", "Amount", "Cost/Unit", "Total Cost"]
        click.echo(tabulate(lot_data, headers=headers, tablefmt="simple"))


@cli.command()
@click.option('--year', '-y', type=int, required=True, help='Tax year')
@click.option('--output', '-o', help='Output file (JSON)')
@click.pass_obj
def tax_report(portfolio_service, year, output):
    """Generate tax report for a year"""
    if not portfolio_service.load_portfolio():
        click.secho("No portfolio found. Run 'init' first.", fg='yellow')
        return

    click.echo(f"Generating tax report for {year}...")
    report = portfolio_service.generate_tax_report(year)

    summary = report['summary']

    click.echo(f"\n📋 Tax Report - {year}")
    click.echo("=" * 50)

    click.echo("\nShort-Term Capital Gains/Losses:")
    click.echo(f"  Gains: ${summary['short_term_gains']:,.2f}")
    click.echo(f"  Losses: ${summary['short_term_losses']:,.2f}")
    click.echo(f"  Net: ${summary['net_short_term']:,.2f}")

    click.echo("\nLong-Term Capital Gains/Losses:")
    click.echo(f"  Gains: ${summary['long_term_gains']:,.2f}")
    click.echo(f"  Losses: ${summary['long_term_losses']:,.2f}")
    click.echo(f"  Net: ${summary['net_long_term']:,.2f}")

    click.echo(f"\nTotal Capital Gains/Losses: ${summary['total_gain_loss']:,.2f}")

    if output:
        with open(output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        click.echo(f"\n✓ Report saved to {output}")


@cli.command()
@click.option('--format', '-f',
              type=click.Choice(['json', 'csv']),
              default='json',
              help='Export format')
@click.option('--output', '-o', required=True, help='Output file')
@click.pass_obj
def export(portfolio_service, format, output):
    """Export portfolio data"""
    if not portfolio_service.load_portfolio():
        click.secho("No portfolio found. Run 'init' first.", fg='yellow')
        return

    click.echo(f"Exporting portfolio as {format}...")
    data = portfolio_service.export_portfolio_data(format)

    with open(output, 'w') as f:
        f.write(data)

    click.secho(f"✓ Portfolio exported to {output}", fg='green')


@cli.command()
@click.pass_obj
def reconcile(portfolio_service):
    """Reconcile portfolio and check for issues"""
    if not portfolio_service.load_portfolio():
        click.secho("No portfolio found. Run 'init' first.", fg='yellow')
        return

    click.echo("Reconciling portfolio...")
    result = portfolio_service.reconcile_portfolio()

    if result['is_valid']:
        click.secho("✓ Portfolio is valid. No issues found.", fg='green')
    else:
        click.secho(f"⚠ Found {len(result['issues'])} issues:", fg='yellow')

        for issue in result['issues']:
            click.echo(f"\n- {issue['type'].upper()}")
            for key, value in issue.items():
                if key != 'type':
                    click.echo(f"  {key}: {value}")


@cli.command()
@click.pass_context
def dashboard(ctx):
    """Launch the web dashboard"""
    from src.presentation.dashboard.app import CryptoPortfolioDashboard

    portfolio_service = ctx.obj

    if not portfolio_service.load_portfolio():
        click.secho("No portfolio found. Run 'init' first.", fg='yellow')
        return

    click.echo("Starting dashboard...")
    click.echo("Dashboard will be available at: http://localhost:8050")
    click.echo("Press Ctrl+C to stop\n")

    dashboard = CryptoPortfolioDashboard(portfolio_service)
    dashboard.run(debug=False, port=8050)
