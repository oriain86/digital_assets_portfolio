# quick_start.py - Quick setup script for the crypto portfolio tracker

import os
import sys
from pathlib import Path


def create_project_structure():
    """Create the complete project directory structure."""

    print("Creating project structure...")

    # Define directory structure
    directories = [
        "src/core/entities",
        "src/core/interfaces",
        "src/core/value_objects",
        "src/application/services",
        "src/application/use_cases",
        "src/infrastructure/cache",
        "src/infrastructure/data_sources",
        "src/infrastructure/repositories",
        "src/presentation/dashboard/callbacks",
        "src/presentation/dashboard/components",
        "src/presentation/dashboard/layouts",
        "src/presentation/cli",
        "src/shared/utils",
        "data/raw",
        "data/processed",
        "data/cache",
        "tests/unit/core",
        "tests/unit/application",
        "tests/unit/infrastructure",
        "tests/integration",
        "tests/fixtures",
        "docs/api",
        "scripts",
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Create __init__.py files
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            init_file.touch()

    print("✓ Directory structure created")


def create_missing_files():
    """Create any missing supporting files."""

    files_to_create = {
        ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Project specific
data/cache/
data/processed/
*.pkl
*.log

# OS
.DS_Store
Thumbs.db

# Secrets
.env
*.key
""",
        ".env.example": """# API Keys (optional - for extended features)
COINGECKO_API_KEY=
BINANCE_API_KEY=
BINANCE_API_SECRET=

# Configuration
PORTFOLIO_NAME=My Crypto Portfolio
COST_BASIS_METHOD=FIFO
RISK_FREE_RATE=0.02
""",
        "Makefile": """# Makefile for crypto portfolio tracker

.PHONY: install run test clean

install:
	pip install -r requirements.txt

run:
	python main.py

test:
	python -m pytest tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf data/cache/*

setup: install
	python quick_start.py

dashboard:
	python main.py

analyze:
	python -m scripts.analyze_portfolio
""",
    }

    for filename, content in files_to_create.items():
        file_path = Path(filename)
        if not file_path.exists():
            file_path.write_text(content)
            print(f"✓ Created {filename}")


def check_csv_file():
    """Check if the CSV file exists and provide guidance."""

    csv_path = Path("data/raw/portfolio_transactions copy.csv")

    if not csv_path.exists():
        print("\n⚠️  CSV file not found!")
        print(f"Please place your transaction CSV file at: {csv_path}")
        print("\nThe CSV should have these columns:")
        print("- timestamp")
        print("- type (Buy, Sell, Deposit, Withdrawal, etc.)")
        print("- asset (BTC, ETH, etc.)")
        print("- amount")
        print("- price_usd")
        print("- total_usd")
        print("- fee_usd")
        print("- exchange")
        print("- transaction_id")
        print("- notes (optional)")

        # Create a sample CSV
        sample_csv = """timestamp,type,asset,amount,price_usd,total_usd,fee_usd,exchange,transaction_id,notes
2024-01-01 10:00:00,Buy,BTC,0.1,45000,4500,10,Coinbase,tx_001,Initial BTC purchase
2024-01-02 14:30:00,Buy,ETH,1.5,2500,3750,8,Coinbase,tx_002,ETH investment
2024-01-15 09:00:00,Sell,BTC,0.05,48000,2400,5,Coinbase,tx_003,Taking some profit
"""
        sample_path = Path("data/raw/sample_transactions.csv")
        sample_path.write_text(sample_csv)
        print(f"\n✓ Created sample CSV at: {sample_path}")
        print("You can use this as a template for your own data.")

        return False
    else:
        print(f"✓ CSV file found at: {csv_path}")
        return True


def check_dependencies():
    """Check if all required dependencies are installed."""

    print("\nChecking dependencies...")

    required_packages = [
        'pandas',
        'numpy',
        'dash',
        'plotly',
        'requests',
        'scipy'
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} not installed")

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False

    return True


def main():
    """Main setup function."""

    print("🚀 Crypto Portfolio Tracker - Quick Setup")
    print("=" * 50)

    # Create project structure
    create_project_structure()

    # Create missing files
    create_missing_files()

    # Check CSV file
    csv_exists = check_csv_file()

    # Check dependencies
    deps_ok = check_dependencies()

    print("\n" + "=" * 50)

    if csv_exists and deps_ok:
        print("✅ Setup complete! You're ready to go.")
        print("\nRun the application with:")
        print("  python main.py")
    else:
        print("⚠️  Setup incomplete. Please:")
        if not csv_exists:
            print("  1. Add your transaction CSV file")
        if not deps_ok:
            print("  2. Install missing dependencies")
        print("\nThen run this script again.")

    print("\nFor more information, see README.md")


if __name__ == "__main__":
    main()
