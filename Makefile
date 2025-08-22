# Makefile for Crypto Portfolio Tracker

.PHONY: help install install-dev setup clean test lint format run dashboard cli docker-build docker-run backup migrate init update

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
PIP := pip
PROJECT_NAME := crypto-portfolio-tracker
DOCKER_IMAGE := $(PROJECT_NAME):latest
PORT := 8050

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Crypto Portfolio Tracker - Available Commands$(NC)"
	@echo "=============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

setup: install ## Complete project setup
	@echo "$(BLUE)Setting up project...$(NC)"
	$(PYTHON) quick_start.py
	@echo "$(GREEN)✓ Project setup complete$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "1. Place your CSV file in data/raw/portfolio_transactions copy.csv"
	@echo "2. Run 'make init' to initialize your portfolio"
	@echo "3. Run 'make run' to start the dashboard"

clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

test: ## Run tests with pytest
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTHON) -m pytest tests/ -v

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

lint: ## Run code linting
	@echo "$(BLUE)Running linters...$(NC)"
	$(PYTHON) -m pylint src/ || true
	$(PYTHON) -m flake8 src/ --max-line-length=120 || true
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m isort src/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	$(PYTHON) -m mypy src/ --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking complete$(NC)"

run: ## Run the main application (dashboard)
	@echo "$(BLUE)Starting Crypto Portfolio Tracker...$(NC)"
	$(PYTHON) main.py

dashboard: run ## Alias for run - start the dashboard

cli: ## Show CLI help
	@echo "$(BLUE)Crypto Portfolio Tracker CLI$(NC)"
	$(PYTHON) -m src.presentation.cli.commands --help

init: ## Initialize portfolio from CSV
	@echo "$(BLUE)Initializing portfolio...$(NC)"
	$(PYTHON) -m src.presentation.cli.commands init -c "data/raw/portfolio_transactions copy.csv"

update: ## Update portfolio prices
	@echo "$(BLUE)Updating prices...$(NC)"
	$(PYTHON) -m src.presentation.cli.commands update

status: ## Show portfolio status
	$(PYTHON) -m src.presentation.cli.commands status

tax-report: ## Generate tax report for current year
	$(PYTHON) -m src.presentation.cli.commands tax-report -y $(shell date +%Y)

backup: ## Create a backup of all data
	@echo "$(BLUE)Creating backup...$(NC)"
	$(PYTHON) scripts/migrate_data.py backup
	@echo "$(GREEN)✓ Backup complete$(NC)"

restore: ## Restore from latest backup
	@echo "$(BLUE)Restoring from backup...$(NC)"
	@echo "$(RED)Warning: This will overwrite current data!$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(PYTHON) scripts/migrate_data.py restore; \
	fi

migrate: ## Migrate data to different format
	@echo "$(BLUE)Data migration options:$(NC)"
	$(PYTHON) scripts/migrate_data.py --help

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)✓ Docker image built: $(DOCKER_IMAGE)$(NC)"

docker-run: ## Run application in Docker
	@echo "$(BLUE)Running in Docker...$(NC)"
	docker run -d \
		--name $(PROJECT_NAME) \
		-p $(PORT):$(PORT) \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/logs:/app/logs \
		$(DOCKER_IMAGE)
	@echo "$(GREEN)✓ Container started$(NC)"
	@echo "Access dashboard at: http://localhost:$(PORT)"

docker-stop: ## Stop Docker container
	@echo "$(BLUE)Stopping Docker container...$(NC)"
	docker stop $(PROJECT_NAME) || true
	docker rm $(PROJECT_NAME) || true
	@echo "$(GREEN)✓ Container stopped$(NC)"

docker-compose-up: ## Start with docker-compose
	docker-compose up -d

docker-compose-down: ## Stop docker-compose services
	docker-compose down

dev: install-dev ## Set up development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	pre-commit install || true
	@echo "$(GREEN)✓ Development environment ready$(NC)"

analyze: ## Analyze portfolio performance
	$(PYTHON) scripts/analyze_portfolio.py

check: lint type-check test ## Run all checks (lint, type-check, test)
	@echo "$(GREEN)✓ All checks passed$(NC)"

release: clean check ## Prepare for release
	@echo "$(BLUE)Preparing release...$(NC)"
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "$(GREEN)✓ Release packages created in dist/$(NC)"

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	cd docs && $(MAKE) html
	@echo "$(GREEN)✓ Documentation generated in docs/_build/html/$(NC)"

serve-docs: ## Serve documentation locally
	cd docs/_build/html && $(PYTHON) -m http.server 8080

.PHONY: quick-test
quick-test: ## Run quick tests only
	$(PYTHON) -m pytest tests/unit -v --tb=short

.PHONY: integration-test
integration-test: ## Run integration tests
	$(PYTHON) -m pytest tests/integration -v

# Development shortcuts
.PHONY: fix
fix: format lint ## Format and lint code

.PHONY: all
all: clean setup test run ## Clean, setup, test, and run

# Show current portfolio value
.PHONY: value
value: ## Show current portfolio value
	@$(PYTHON) -c "from src.application.services.portfolio_service import PortfolioService; \
	s = PortfolioService(); \
	s.load_portfolio() and print(f'Portfolio Value: $${s.get_portfolio().get_total_value():,.2f}')"
