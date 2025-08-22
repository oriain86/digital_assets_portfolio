# diagnostic_check.py

# Run this script to diagnose why the initial portfolio value is incorrect

from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd


def diagnose_initial_value(csv_path: str):
    """Diagnose why initial portfolio value on Aug 23, 2023 is incorrect."""

    # Read the CSV file
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    target_date = datetime(2023, 8, 23)

    print("=" * 80)
    print(f"DIAGNOSTIC: Portfolio value on {target_date.date()}")
    print("=" * 80)

    # Get all transactions up to and including Aug 23, 2023
    mask = df['timestamp'] <= target_date + timedelta(days=1)
    transactions_before = df[mask].copy()

    print(f"\nTotal transactions up to Aug 23, 2023: {len(transactions_before)}")

    # Calculate running balances
    balances = {}

    for _, tx in transactions_before.iterrows():
        asset = tx['asset']
        amount = Decimal(str(tx['amount']))
        tx_type = tx['type']

        if asset not in balances:
            balances[asset] = Decimal('0')

        if tx_type in ['Buy', 'Receive', 'Transfer In', 'Convert (to)', 'Reward / Bonus', 'Interest']:
            balances[asset] += amount
        elif tx_type in ['Sell', 'Send', 'Transfer Out', 'Convert (from)']:
            balances[asset] -= amount
        elif tx_type == 'Deposit' and asset == 'USD':
            balances[asset] += amount
        elif tx_type == 'Withdrawal' and asset == 'USD':
            balances[asset] -= amount

    # Show non-zero balances
    print("\nAsset balances on Aug 23, 2023:")
    print("-" * 40)

    stablecoins = ['USD', 'USDT', 'USDC', 'DAI', 'BUSD']

    total_value = Decimal('0')

    for asset, balance in sorted(balances.items()):
        if balance > 0:
            if asset in stablecoins:
                value = balance
                total_value += value
                print(f"{asset:10} {float(balance):15.4f} = ${float(value):10.2f}")
            else:
                # For crypto, we'd need price data
                print(f"{asset:10} {float(balance):15.4f} = [needs price]")

    print("-" * 40)
    print(f"Stablecoin/USD total: ${float(total_value):,.2f}")

    # Show transactions around Aug 23
    print("\n\nTransactions around Aug 23, 2023:")
    print("-" * 80)

    start_window = target_date - timedelta(days=7)
    end_window = target_date + timedelta(days=7)

    window_mask = (df['timestamp'] >= start_window) & (df['timestamp'] <= end_window)
    window_txs = df[window_mask].copy()

    for _, tx in window_txs.iterrows():
        date_str = tx['timestamp'].strftime('%Y-%m-%d')
        print(f"{date_str} | {tx['type']:15} | {tx['asset']:8} | "
              f"Amount: {tx['amount']:12} | USD: {tx.get('total_usd', 'N/A')}")

    # Check for any large crypto positions
    print("\n\nLarge crypto positions (> 0.1 units):")
    print("-" * 40)

    for asset, balance in sorted(balances.items()):
        if asset not in stablecoins and balance > 0.1:
            print(f"{asset}: {float(balance):.4f} units")

    return balances


# Run this with your CSV file
if __name__ == "__main__":
    # Update this path to your CSV file
    csv_path = "data/portfolio_transactions.csv"

    try:
        balances = diagnose_initial_value(csv_path)
    except FileNotFoundError:
        print(f"Error: Could not find file at '{csv_path}'")
        print("\nPlease check your data directory for the CSV file.")
        print("Common locations:")
        print("  - data/transactions.csv")
        print("  - data/crypto_transactions.csv")
        print("  - data/portfolio_transactions.csv")

        # Try to list files in data directory
        import os

        if os.path.exists("data"):
            print("\nFiles in data directory:")
            for file in os.listdir("data"):
                if file.endswith('.csv'):
                    print(f"  - data/{file}")
    except Exception as e:
        print(f"Error: {e}")