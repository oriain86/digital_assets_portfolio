# test_application.py

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from src.core.entities.transaction import Transaction, TransactionType
        print("✓ Core entities imported")

        from src.infrastructure.repositories.transaction_repository import SQLiteTransactionRepository
        print("✓ Repository imported")

        from src.application.services.portfolio_service import PortfolioService
        print("✓ Portfolio service imported")

        from src.config.settings import settings
        print("✓ Settings imported")

        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_repository():
    """Test repository functionality."""
    print("\nTesting repository...")
    try:
        from src.infrastructure.repositories.transaction_repository import SQLiteTransactionRepository
        from src.core.entities.transaction import Transaction, TransactionType
        from decimal import Decimal

        # Create test repository
        repo = SQLiteTransactionRepository("data/test_transactions.db")
        print("✓ Repository created")

        # Create test transaction
        tx = Transaction(
            timestamp=datetime.now(),
            type=TransactionType.BUY,
            asset="BTC",
            amount=Decimal("0.1"),
            price_usd=Decimal("50000"),
            total_usd=Decimal("5000"),
            fee_usd=Decimal("10"),
            exchange="Test Exchange"
        )

        # Save transaction
        repo.save(tx)
        print("✓ Transaction saved")

        # Retrieve transaction
        retrieved = repo.get_by_id(tx.transaction_id)
        if retrieved:
            print("✓ Transaction retrieved")
            print(f"  - ID: {retrieved.transaction_id}")
            print(f"  - Asset: {retrieved.asset}")
            print(f"  - Amount: {retrieved.amount}")

        # Get all transactions
        all_txs = repo.get_all()
        print(f"✓ Total transactions in test DB: {len(all_txs)}")

        # Clean up
        Path("data/test_transactions.db").unlink(missing_ok=True)

        return True
    except Exception as e:
        print(f"✗ Repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_csv_loading():
    """Test CSV loading functionality."""
    print("\nTesting CSV loading...")

    # Check if CSV exists
    csv_path = Path("data/raw/portfolio_transactions.csv")
    if not csv_path.exists():
        print(f"⚠ CSV file not found at: {csv_path}")
        print("  Creating sample CSV for testing...")

        # Create sample CSV
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        sample_csv = """timestamp,type,asset,amount,price_usd,total_usd,fee_usd,exchange,transaction_id,notes
2024-01-01 10:00:00,Buy,BTC,0.1,45000,4500,10,Coinbase,test_001,Test purchase
2024-01-02 14:30:00,Buy,ETH,1.5,2500,3750,8,Coinbase,test_002,Test ETH buy
2024-01-15 09:00:00,Sell,BTC,0.05,48000,2400,5,Coinbase,test_003,Taking profit
"""
        csv_path.write_text(sample_csv)
        print("✓ Sample CSV created")

    try:
        from src.infrastructure.data_sources.unified_csv_loader import UnifiedCSVLoader

        loader = UnifiedCSVLoader()
        transactions = loader.load_transactions(str(csv_path))

        print(f"✓ Loaded {len(transactions)} transactions from CSV")

        if loader.errors:
            print(f"⚠ Found {len(loader.errors)} errors:")
            for error in loader.errors[:3]:
                print(f"  - {error}")

        return len(transactions) > 0
    except Exception as e:
        print(f"✗ CSV loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_portfolio_service():
    """Test portfolio service."""
    print("\nTesting portfolio service...")
    try:
        from src.application.services.portfolio_service import PortfolioService

        service = PortfolioService(
            data_path="data",
            cache_path="data/cache",
            cost_basis_method="FIFO"
        )
        print("✓ Portfolio service created")

        # Try to load existing portfolio
        if service.load_portfolio():
            print("✓ Loaded existing portfolio")
            portfolio = service.get_portfolio()
            print(f"  - Total value: ${portfolio.get_total_value():.2f}")
            print(f"  - Positions: {len([p for p in portfolio.positions.values() if p.current_amount > 0])}")
        else:
            print("ℹ No existing portfolio found (this is OK for first run)")

        return True
    except Exception as e:
        print(f"✗ Portfolio service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Crypto Portfolio Tracker")
    print("=" * 50)

    tests = [
        ("Imports", test_imports),
        ("Repository", test_repository),
        ("CSV Loading", test_csv_loading),
        ("Portfolio Service", test_portfolio_service)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(tests)} tests passed")

    if total_passed == len(tests):
        print("\n🎉 All tests passed! Ready to run the application.")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. Or use minimal version: python main_minimal.py")
    else:
        print("\n⚠ Some tests failed. Please fix the issues before running the application.")


if __name__ == "__main__":
    main()
