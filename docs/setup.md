# Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Installation](#detailed-installation)
4. [Configuration](#configuration)
5. [Data Preparation](#data-preparation)
6. [Running the Application](#running-the-application)
7. [Docker Setup](#docker-setup)
8. [Troubleshooting](#troubleshooting)
9. [Development Setup](#development-setup)

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher (3.9+ recommended)
- **Operating System**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended for large portfolios)
- **Storage**: 500MB free space

### Software Dependencies
```bash
# Check Python version
python --version  # Should be 3.8+

# Check pip is installed
pip --version
```

## Quick Start

The fastest way to get started:

```bash
# 1. Clone the repository
git clone <repository-url>
cd crypto-portfolio-tracker

# 2. Run the quick setup script
python quick_start.py

# 3. Install dependencies
pip install -r requirements.txt

# 4. Place your CSV file in data/raw/
cp /path/to/your/transactions.csv "data/raw/portfolio_transactions copy.csv"

# 5. Run the application
python main.py
```

## Detailed Installation

### Step 1: Set Up Python Environment

#### Option A: Using venv (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Option B: Using Conda
```bash
# Create conda environment
conda create -n crypto-portfolio python=3.9
conda activate crypto-portfolio
```

### Step 2: Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Development dependencies (optional)
pip install -r requirements-dev.txt
```

#### Manual Installation (if requirements.txt fails)
```bash
pip install pandas==1.5.3
pip install numpy==1.24.3
pip install dash==2.14.1
pip install plotly==5.17.0
pip install requests==2.31.0
pip install python-dateutil==2.8.2
pip install scipy==1.11.4
pip install openpyxl==3.1.2  # For Excel support
pip install click==8.1.7     # For CLI
pip install tabulate==0.9.0  # For CLI tables
```

### Step 3: Create Project Structure

```bash
# Run the setup script
python quick_start.py

# Or manually create directories
mkdir -p data/{raw,processed,cache}
mkdir -p logs
mkdir -p tests
mkdir -p scripts
```

### Step 4: Verify Installation

```bash
# Run the test script
python -c "from src.core.entities.transaction import Transaction; print('✓ Import test passed')"

# Run unit tests
python -m pytest tests/
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Portfolio Settings
PORTFOLIO_NAME=My Crypto Portfolio
COST_BASIS_METHOD=FIFO  # Options: FIFO, LIFO, HIFO
BASE_CURRENCY=USD
RISK_FREE_RATE=0.02

# Dashboard Settings
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8050
DASHBOARD_DEBUG=False

# API Settings (Optional)
COINGECKO_API_KEY=your_api_key_here  # For higher rate limits

# Cache Settings
PRICE_CACHE_DURATION=5  # Minutes
METRICS_CACHE_DURATION=60  # Minutes

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=True
LOG_TO_CONSOLE=True
```

### Settings File

Alternative to environment variables, edit `src/config/settings.py`:

```python
class Settings:
    # Modify default values here
    DEFAULT_COST_BASIS_METHOD = "FIFO"
    DASHBOARD_PORT = 8050
    # ... other settings
```

## Data Preparation

### CSV File Format

Your transaction CSV must have these columns:

| Column | Required | Format | Example |
|--------|----------|--------|---------|
| timestamp | Yes | YYYY-MM-DD HH:MM:SS | 2024-01-15 14:30:00 |
| type | Yes | Text | Buy, Sell, Deposit, etc. |
| asset | Yes | Text | BTC, ETH, USD |
| amount | Yes | Number | 0.5 |
| price_usd | No* | Number | 45000.00 |
| total_usd | No* | Number | 22500.00 |
| fee_usd | No | Number | 10.00 |
| exchange | No | Text | Coinbase |
| transaction_id | No | Text | tx_123456 |
| notes | No | Text | Initial purchase |

*Either price_usd or total_usd should be provided for Buy/Sell transactions

### Supported Transaction Types
- **Buy**: Purchase of crypto
- **Sell**: Sale of crypto
- **Deposit**: Fiat or crypto deposit
- **Withdrawal**: Fiat or crypto withdrawal
- **Send**: Transfer out
- **Receive**: Transfer in
- **Convert (from)**: Source of conversion
- **Convert (to)**: Destination of conversion
- **Reward / Bonus**: Staking rewards, airdrops
- **Interest**: Interest earned

### Sample CSV
```csv
timestamp,type,asset,amount,price_usd,total_usd,fee_usd,exchange,transaction_id,notes
2024-01-01 10:00:00,Deposit,USD,10000,,10000,,Bank,,Initial deposit
2024-01-02 14:30:00,Buy,BTC,0.25,40000,10000,20,Coinbase,tx_001,First BTC purchase
2024-01-10 09:15:00,Buy,ETH,5,2000,10000,15,Coinbase,tx_002,ETH investment
```

### Data Validation

Before importing, ensure:
1. **Dates are consistent**: Use the same format throughout
2. **No negative amounts**: All amounts should be positive
3. **Matching conversions**: Convert (from) and Convert (to) should pair up
4. **Chronological order**: Recommended but not required

## Running the Application

### Command Line Interface

```bash
# Initialize portfolio from CSV
python -m src.presentation.cli.commands init -c "data/raw/portfolio_transactions copy.csv"

# Check portfolio status
python -m src.presentation.cli.commands status

# Update prices
python -m src.presentation.cli.commands update

# Generate tax report
python -m src.presentation.cli.commands tax-report -y 2024

# Export portfolio data
python -m src.presentation.cli.commands export -f json -o portfolio_export.json

# Launch dashboard
python -m src.presentation.cli.commands dashboard
```

### Direct Python Execution

```bash
# Run main application (launches dashboard)
python main.py

# Run specific scripts
python scripts/analyze_portfolio.py
python scripts/migrate_data.py backup
```

### Dashboard Access

After running `python main.py`:
1. Open your web browser
2. Navigate to: http://localhost:8050
3. Dashboard will load automatically

## Docker Setup

### Quick Docker Run

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t crypto-portfolio-tracker .

# Run container
docker run -d \
  --name portfolio-tracker \
  -p 8050:8050 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  crypto-portfolio-tracker
```

### Docker Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - PORTFOLIO_NAME=My Crypto Portfolio
  - COST_BASIS_METHOD=FIFO
  - DASHBOARD_PORT=8050
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```
ImportError: No module named 'src'
```
**Solution**: Run from project root directory:
```bash
cd /path/to/crypto-portfolio-tracker
python main.py
```

#### 2. CSV Not Found
```
FileNotFoundError: portfolio_transactions copy.csv
```
**Solution**: Ensure file is in correct location:
```bash
cp your_file.csv "data/raw/portfolio_transactions copy.csv"
```

#### 3. Price Fetch Failures
```
Warning: Price update failed
```
**Solutions**:
- Check internet connection
- Wait 1-2 minutes (rate limit)
- Use cached prices

#### 4. Memory Issues with Large Portfolios
**Solutions**:
- Increase Python heap size: `python -Xmx4g main.py`
- Process transactions in batches
- Use Docker with memory limits

#### 5. Dashboard Not Loading
**Solutions**:
- Check if port 8050 is available: `netstat -an | grep 8050`
- Try different port: `DASHBOARD_PORT=8051 python main.py`
- Disable firewall temporarily

### Debug Mode

Enable detailed logging:

```bash
# Set debug environment variable
export LOG_LEVEL=DEBUG
export DASHBOARD_DEBUG=True

# Run with verbose output
python -v main.py
```

### Checking Logs

```bash
# View latest logs
tail -f logs/portfolio_*.log

# Check error logs
tail -f logs/errors.log
```

## Development Setup

### IDE Configuration

#### PyCharm
1. Open project root folder
2. Right-click `src` → Mark Directory as → Sources Root
3. Configure interpreter to use virtual environment
4. Install requirements

#### VS Code
1. Open project root folder
2. Create `.vscode/settings.json`:
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "python.autoComplete.extraPaths": ["./src"]
}
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src tests/

# Run specific test file
python -m pytest tests/test_basic_functionality.py

# Run with verbose output
python -m pytest -v
```

### Code Quality

```bash
# Format code
black src/

# Lint code
pylint src/

# Type checking
mypy src/
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-metric

# Make changes and test
# ...

# Commit changes
git add .
git commit -m "Add new metric calculation"

# Push to remote
git push origin feature/new-metric
```

## Performance Optimization

### Large Portfolio Tips

1. **Batch Processing**
   ```python
   # In settings.py
   BATCH_SIZE = 5000  # Process transactions in batches
   ```

2. **Disable Auto-refresh**
   ```python
   # Increase interval in app.py
   interval=5*60*1000  # 5 minutes instead of 1
   ```

3. **Use Production Mode**
   ```bash
   export DASHBOARD_DEBUG=False
   python main.py
   ```

4. **Optimize Database**
   ```bash
   # Vacuum SQLite database
   sqlite3 data/transactions.db "VACUUM;"
   ```

## Backup and Recovery

### Creating Backups

```bash
# Backup all data
python scripts/migrate_data.py backup

# Backup specific date
python scripts/migrate_data.py backup --date 2024-01-01
```

### Restoring from Backup

```bash
# List available backups
ls backups/

# Restore specific backup
python scripts/migrate_data.py restore backups/backup_20240101_120000
```

## Next Steps

1. **Explore the Dashboard**: Familiarize yourself with all features
2. **Customize Metrics**: Modify `metrics_calculator.py` for custom metrics
3. **Add Price Sources**: Extend `price_service.py` for more exchanges
4. **Create Reports**: Use CLI to generate tax and performance reports
5. **Automate Updates**: Set up cron job for daily price updates

## Getting Help

- Check the [Architecture Guide](architecture.md) for system design
- Review example transactions in `tests/fixtures/sample_data.py`
- Enable debug logging for detailed error messages
- Open an issue on GitHub for bugs or feature requests
- 