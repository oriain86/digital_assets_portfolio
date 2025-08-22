# Architecture Documentation

## Overview

The Crypto Portfolio Tracker follows **Clean Architecture** principles (also known as Hexagonal Architecture or Ports and Adapters) to ensure maintainability, testability, and scalability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Presentation Layer                         │
│  ┌─────────────────────┐        ┌─────────────────────────────┐   │
│  │    CLI Interface    │        │    Dashboard (Dash/Plotly)   │   │
│  │  - commands.py      │        │  - app.py                    │   │
│  │  - Quick actions    │        │  - Components & Callbacks    │   │
│  └─────────────────────┘        └─────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
┌───────────────────────────────────┴─────────────────────────────────┐
│                          Application Layer                          │
│  ┌─────────────────────┐        ┌─────────────────────────────┐   │
│  │    Use Cases        │        │      Services              │   │
│  │  - Load data        │        │  - Portfolio Service       │   │
│  │  - Calculate metrics│        │  - Transaction Processor   │   │
│  │  - Generate reports │        │  - Metrics Calculator      │   │
│  └─────────────────────┘        └─────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
┌───────────────────────────────────┴─────────────────────────────────┐
│                            Core Domain                              │
│  ┌─────────────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │     Entities        │  │  Interfaces  │  │  Value Objects  │   │
│  │  - Transaction      │  │  - Repository│  │  - Money        │   │
│  │  - Position         │  │  - DataSource│  │  - Percentage   │   │
│  │  - Portfolio        │  │              │  │  - TimePeriod   │   │
│  └─────────────────────┘  └──────────────┘  └─────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
┌───────────────────────────────────┴─────────────────────────────────┐
│                         Infrastructure Layer                        │
│  ┌─────────────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Data Sources      │  │ Repositories │  │     Cache       │   │
│  │  - CSV Loader       │  │  - SQLite    │  │  - Price Cache  │   │
│  │  - Price APIs       │  │  - File      │  │  - Redis (opt)  │   │
│  └─────────────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Principles

### 1. **Dependency Rule**
Dependencies only point inward. The inner layers don't know about the outer layers:
- Core domain has no external dependencies
- Application layer depends only on Core
- Infrastructure and Presentation depend on Application and Core

### 2. **Separation of Concerns**
Each layer has a specific responsibility:
- **Core**: Business logic and domain rules
- **Application**: Use cases and orchestration
- **Infrastructure**: External systems and data persistence
- **Presentation**: User interfaces and API endpoints

### 3. **Testability**
Each component can be tested in isolation:
- Domain entities have pure business logic
- Use cases can be tested with mock repositories
- Infrastructure can be swapped out (e.g., SQLite to PostgreSQL)

## Layer Details

### Core Domain Layer

**Purpose**: Contains the business logic that is independent of any framework or external system.

**Components**:
- **Entities**: Core business objects with behavior
  - `Transaction`: Represents a single crypto transaction
  - `Position`: Tracks holdings and cost basis for an asset
  - `Portfolio`: Manages all positions and overall performance

- **Value Objects**: Immutable objects that represent concepts
  - `Money`: Precise decimal arithmetic for financial calculations
  - `Percentage`: Percentage calculations
  - `TimePeriod`: Date range operations

- **Interfaces**: Contracts that infrastructure must implement
  - `Repository`: Abstract data persistence
  - `DataSource`: Abstract data loading

**Key Design Decisions**:
- Entities are rich domain models, not anemic data structures
- All monetary calculations use Decimal for precision
- Cost basis tracking supports FIFO, LIFO, and HIFO methods
- Transaction matching for conversions is handled automatically

### Application Layer

**Purpose**: Orchestrates the flow of data and coordinates domain objects to perform specific tasks.

**Components**:
- **Use Cases**: Single-purpose operations
  - `LoadTransactionsUseCase`: Loads and validates transaction data
  - `CalculateMetricsUseCase`: Computes portfolio metrics
  - `GenerateReportUseCase`: Creates various report types

- **Services**: Complex orchestration logic
  - `PortfolioService`: Main service coordinating portfolio operations
  - `TransactionProcessor`: Handles transaction parsing and validation
  - `MetricsCalculator`: Advanced financial metrics calculations

**Key Design Decisions**:
- Use cases follow Single Responsibility Principle
- Services handle cross-cutting concerns
- All operations return result objects with success/error states

### Infrastructure Layer

**Purpose**: Implements interfaces defined by the core domain and handles all external concerns.

**Components**:
- **Data Sources**:
  - `UnifiedCSVLoader`: Parses CSV transaction files
  - `PriceService`: Fetches current/historical prices from APIs

- **Repositories**:
  - `SQLiteTransactionRepository`: Persists transactions to SQLite
  - `FilePortfolioRepository`: Saves portfolio state to disk

- **Cache**:
  - `PriceCache`: Reduces API calls with time-based caching

**Key Design Decisions**:
- Repository pattern allows swapping storage mechanisms
- Price caching prevents API rate limit issues
- CSV parsing handles multiple date formats and edge cases

### Presentation Layer

**Purpose**: Handles user interaction and displays information.

**Components**:
- **Dashboard**: Interactive web interface using Plotly Dash
  - Real-time portfolio value tracking
  - Interactive charts and metrics
  - Position management and analysis

- **CLI**: Command-line interface for quick operations
  - Portfolio status checks
  - Report generation
  - Data import/export

**Key Design Decisions**:
- Dashboard updates reactively to data changes
- Components are modular and reusable
- Dark theme for better data visualization

## Data Flow Example

Here's how a typical operation flows through the architecture:

```
1. User uploads CSV file through Dashboard
   ↓
2. Presentation layer calls LoadTransactionsUseCase
   ↓
3. Use case calls UnifiedCSVLoader (Infrastructure)
   ↓
4. CSV Loader returns raw transaction data
   ↓
5. Use case creates Transaction entities (Core)
   ↓
6. Use case calls PortfolioService to process transactions
   ↓
7. Portfolio Service updates Position entities
   ↓
8. Portfolio Service saves state via Repository
   ↓
9. Dashboard receives updated portfolio data
   ↓
10. Dashboard components render new visualizations
```

## Design Patterns Used

### 1. **Repository Pattern**
- Abstracts data persistence
- Allows switching between SQLite, PostgreSQL, etc.
- Example: `TransactionRepository` interface

### 2. **Factory Pattern**
- Creates complex objects
- Example: Transaction creation with validation

### 3. **Strategy Pattern**
- Different cost basis calculation methods
- FIFO, LIFO, HIFO strategies

### 4. **Observer Pattern**
- Dashboard components observe portfolio changes
- Reactive updates via Dash callbacks

### 5. **Command Pattern**
- CLI commands encapsulate operations
- Each command is self-contained

## Error Handling Strategy

1. **Domain Exceptions**: Custom exceptions for business rule violations
2. **Validation Errors**: Caught at boundaries and reported clearly
3. **Result Objects**: Operations return success/failure with details
4. **Graceful Degradation**: Missing prices don't crash the system

## Performance Considerations

1. **Lazy Loading**: Positions calculate metrics on-demand
2. **Batch Processing**: Transactions processed in batches
3. **Caching**: Price data cached to reduce API calls
4. **Efficient Algorithms**: Heap-based FIFO/LIFO calculations

## Security Considerations

1. **No Credentials in Code**: API keys in environment variables
2. **Input Validation**: All user input sanitized
3. **Local Storage**: Sensitive data stays on user's machine
4. **No External Data Sharing**: All processing is local

## Extensibility Points

1. **New Asset Types**: Add new asset classes (stocks, bonds)
2. **Exchange Integration**: Direct API connections
3. **Tax Strategies**: Additional tax calculation methods
4. **Report Formats**: New export formats
5. **Real-time Updates**: WebSocket price feeds

## Technology Stack

- **Core**: Python 3.9+ with type hints
- **Web Framework**: Dash/Plotly for interactive dashboards
- **Data Processing**: Pandas, NumPy for calculations
- **Storage**: SQLite for transactions, Pickle for portfolio state
- **Testing**: Pytest for unit and integration tests
- **Deployment**: Docker for containerization

## Future Architecture Considerations

1. **Microservices**: Split into separate services if needed
2. **Event Sourcing**: Track all portfolio changes as events
3. **CQRS**: Separate read and write models for performance
4. **Cloud Native**: Deploy to AWS/GCP with managed services
5. **Multi-user**: Add authentication and user isolation
6. 