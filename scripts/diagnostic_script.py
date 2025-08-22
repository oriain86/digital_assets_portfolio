# diagnostic_script.py

# Run this to identify which transactions are causing drops

from datetime import datetime, timedelta
from src.application.services.portfolio_service import PortfolioService


def diagnose_portfolio_drops():
    """Diagnose portfolio value drops."""

    ps = PortfolioService()
    ps.load_portfolio()

    print("\n🔍 Analyzing Portfolio for Artificial Drops\n")
    print("=" * 60)

    # Get transfer summary
    transfer_summary = ps.get_transfer_summary()

    print("\n📦 Cold Storage Analysis:")
    print("-" * 40)

    for asset, info in transfer_summary['assets_with_transfers'].items():
        if info['likely_in_cold_storage'] > 0:
            print(f"\n{asset}:")
            print(f"  Transferred Out: {info['transferred_out']:.4f}")
            print(f"  Transferred In:  {info['transferred_in']:.4f}")
            print(f"  Still in Cold:   {info['likely_in_cold_storage']:.4f}")

    print(f"\nTotal estimated value in cold storage: ${transfer_summary['estimated_cold_storage_value']:,.2f}")

    # Analyze large single-day drops
    print("\n📉 Large Single-Day Drops Analysis:")
    print("-" * 40)

    metrics = ps.get_portfolio_metrics()
    time_series = metrics.get('time_series', {})

    if time_series and 'dates' in time_series and 'values' in time_series:
        dates = time_series['dates']
        values = time_series['values']

        drops = []
        for i in range(1, len(values)):
            if values[i - 1] > 0:
                daily_change = (values[i] - values[i - 1]) / values[i - 1]
                if daily_change < -0.3:  # More than 30% drop
                    drops.append({
                        'date': dates[i],
                        'prev_value': values[i - 1],
                        'new_value': values[i],
                        'change_pct': daily_change * 100
                    })

        if drops:
            print(f"\nFound {len(drops)} significant drops:\n")
            for drop in drops[:10]:  # Show first 10
                print(
                    f"  {drop['date']}: ${drop['prev_value']:,.0f} → ${drop['new_value']:,.0f} ({drop['change_pct']:.1f}%)")

                # Find transactions on that date
                drop_date = drop['date']
                txs_on_date = []

                for pos in ps.portfolio.positions.values():
                    for tx in pos.transactions:
                        if tx.timestamp.date() == drop_date:
                            txs_on_date.append(tx)

                if txs_on_date:
                    print(f"    Transactions on this date:")
                    for tx in txs_on_date[:3]:
                        print(f"      - {tx.type.value}: {tx.amount:.4f} {tx.asset}")
        else:
            print("No significant single-day drops found (good!)")

    return transfer_summary


if __name__ == "__main__":
    diagnose_portfolio_drops()
