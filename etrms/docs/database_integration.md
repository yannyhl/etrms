# Database Integration for Risk Configurations

This document describes the database integration for risk configurations and circuit breakers in the Enhanced Trading Risk Management System (ETRMS).

## Overview

The ETRMS uses SQLAlchemy as an ORM (Object-Relational Mapping) to interact with the database. The system persists risk configurations and circuit breaker conditions to a PostgreSQL database, allowing for long-term storage and retrieval of risk management settings.

## Database Models

### Risk Configuration Model

The `RiskConfiguration` model stores the general risk parameters for an account:

```python
class RiskConfiguration(Base):
    __tablename__ = "risk_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(String(50), nullable=False)
    account_id = Column(String(50), ForeignKey("accounts.account_id"), nullable=False)
    position_max_drawdown_percentage = Column(Numeric(10, 2), nullable=False)
    position_trailing_stop_multiplier = Column(Numeric(10, 2), nullable=False)
    daily_max_drawdown_percentage = Column(Numeric(10, 2), nullable=False)
    weekly_max_drawdown_percentage = Column(Numeric(10, 2), nullable=False)
    monthly_max_drawdown_percentage = Column(Numeric(10, 2), nullable=False)
    max_position_size_percentage = Column(Numeric(10, 2), nullable=False)
    max_correlated_exposure_percentage = Column(Numeric(10, 2), nullable=False)
    risk_per_trade_percentage = Column(Numeric(10, 2), nullable=False)
    volatility_adjustment_factor = Column(Numeric(10, 2), nullable=False)
    market_regime_thresholds = Column(JSON, nullable=False)
    cooling_off_period_minutes = Column(Integer, nullable=False)
    consecutive_loss_threshold = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
```

### Symbol-Specific Risk Configuration Model

The `SymbolRiskConfiguration` model stores symbol-specific risk parameters:

```python
class SymbolRiskConfiguration(Base):
    __tablename__ = "symbol_risk_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    risk_config_id = Column(Integer, ForeignKey("risk_configurations.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    max_position_size_percentage = Column(Numeric(10, 2), nullable=False)
    max_leverage = Column(Integer, nullable=False)
    position_max_drawdown_percentage = Column(Numeric(10, 2), nullable=False)
    risk_per_trade_percentage = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Circuit Breaker Model

The `CircuitBreaker` model stores circuit breaker conditions:

```python
class CircuitBreaker(Base):
    __tablename__ = "circuit_breakers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    account_id = Column(String(50), ForeignKey("accounts.account_id"), nullable=False)
    condition = Column(Text, nullable=False)
    action = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False)
    symbols = Column(JSON, nullable=True)  # List of symbols this breaker applies to, null means all
    exchanges = Column(JSON, nullable=True)  # List of exchanges this breaker applies to, null means all
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Circuit Breaker Event Model

The `CircuitBreakerEvent` model stores events when circuit breakers are triggered:

```python
class CircuitBreakerEvent(Base):
    __tablename__ = "circuit_breaker_events"
    
    id = Column(Integer, primary_key=True, index=True)
    circuit_breaker_id = Column(Integer, ForeignKey("circuit_breakers.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    triggered_values = Column(JSON, nullable=False)
    action_taken = Column(String(50), nullable=False)
    action_result = Column(JSON, nullable=True)
    positions_affected = Column(JSON, nullable=True)
```

## Repository Pattern

The system uses the repository pattern to isolate the database interaction logic. This provides several benefits:

1. **Separation of Concerns**: Database interaction logic is separated from business logic
2. **Testability**: Repositories can be mocked for unit testing
3. **Code Reuse**: Common database operations are centralized
4. **Error Handling**: Consistent error handling for database operations

Two main repositories are implemented:

1. **RiskConfigurationRepository**: Handles CRUD operations for risk configurations
2. **CircuitBreakerRepository**: Handles CRUD operations for circuit breakers and their events

### RiskConfigurationRepository Methods

- `get_by_id(db, config_id, account_id)`: Get a configuration by ID
- `get_all_for_account(db, account_id)`: Get all configurations for an account
- `create(db, config_data)`: Create a new configuration
- `update(db, config_id, account_id, config_data)`: Update an existing configuration
- `delete(db, config_id, account_id)`: Delete a configuration
- `to_dict(risk_config)`: Convert a configuration to a dictionary

### CircuitBreakerRepository Methods

- `get_by_id(db, breaker_id)`: Get a circuit breaker by ID
- `get_by_name(db, name, account_id)`: Get a circuit breaker by name
- `get_all_for_account(db, account_id)`: Get all circuit breakers for an account
- `create(db, breaker_data)`: Create a new circuit breaker
- `update(db, breaker_id, breaker_data)`: Update an existing circuit breaker
- `delete(db, breaker_id)`: Delete a circuit breaker
- `enable(db, breaker_id)`: Enable a circuit breaker
- `disable(db, breaker_id)`: Disable a circuit breaker
- `log_event(db, event_data)`: Log a circuit breaker event
- `get_events(db, breaker_id, limit)`: Get events for a circuit breaker
- `to_dict(circuit_breaker)`: Convert a circuit breaker to a dictionary
- `event_to_dict(event)`: Convert a circuit breaker event to a dictionary

## RiskMonitor Integration

The `RiskMonitor` class has been updated to use the database repositories for loading and saving risk configurations:

### Load Risk Configuration

```python
async def load_risk_configuration(self, config_id: str, account_id: str, db: Session) -> Dict[str, Any]:
    """
    Load a risk configuration from the database.
    
    Args:
        config_id: The ID of the configuration to load.
        account_id: The ID of the account.
        db: Database session.
        
    Returns:
        The loaded configuration.
    """
    # Implementation using RiskConfigurationRepository and CircuitBreakerRepository
```

### Save Risk Configuration

```python
async def save_risk_configuration(self, config_id: str, account_id: str, db: Session) -> Dict[str, Any]:
    """
    Save the current risk configuration to the database.
    
    Args:
        config_id: The ID to save the configuration under.
        account_id: The ID of the account.
        db: Database session.
        
    Returns:
        The saved configuration.
    """
    # Implementation using RiskConfigurationRepository and CircuitBreakerRepository
```

## API Endpoints

The ETRMS provides the following API endpoints for risk configuration management:

### Risk Configuration Endpoints

- `GET /api/risk/configurations`: Get all risk configurations for an account
- `GET /api/risk/configurations/{config_id}`: Load a risk configuration
- `POST /api/risk/configurations`: Save a risk configuration

### Circuit Breaker Endpoints

- `GET /api/risk/circuit-breakers/all`: Get all circuit breakers for an account
- `POST /api/risk/circuit-breakers/db`: Create a circuit breaker
- `PUT /api/risk/circuit-breakers/db/{breaker_id}`: Update a circuit breaker
- `DELETE /api/risk/circuit-breakers/db/{breaker_id}`: Delete a circuit breaker
- `PUT /api/risk/circuit-breakers/db/{breaker_id}/enable`: Enable a circuit breaker
- `PUT /api/risk/circuit-breakers/db/{breaker_id}/disable`: Disable a circuit breaker
- `GET /api/risk/circuit-breakers/db/{breaker_id}/events`: Get circuit breaker events

## Database Schema Diagram

```
┌───────────────────────────────┐       ┌───────────────────────────────┐
│     risk_configurations       │       │    symbol_risk_configurations │
├───────────────────────────────┤       ├───────────────────────────────┤
│ id (PK)                       │       │ id (PK)                       │
│ config_id                     │       │ risk_config_id (FK)           │
│ account_id (FK)               │◄───┐  │ symbol                        │
│ position_max_drawdown_pct     │    │  │ max_position_size_pct         │
│ position_trailing_stop_mult   │    │  │ max_leverage                  │
│ daily_max_drawdown_pct        │    │  │ position_max_drawdown_pct     │
│ weekly_max_drawdown_pct       │    │  │ risk_per_trade_pct            │
│ monthly_max_drawdown_pct      │    │  │ created_at                    │
│ max_position_size_pct         │    │  │ updated_at                    │
│ max_correlated_exposure_pct   │    └──┤                               │
│ risk_per_trade_pct            │       └───────────────────────────────┘
│ volatility_adjustment_factor  │       
│ market_regime_thresholds      │       ┌───────────────────────────────┐
│ cooling_off_period_minutes    │       │       circuit_breakers        │
│ consecutive_loss_threshold    │       ├───────────────────────────────┤
│ created_at                    │       │ id (PK)                       │
│ updated_at                    │       │ name                          │
│ is_active                     │       │ description                   │
└───────────────────────────────┘       │ account_id (FK)               │
                                        │ condition                     │
                                        │ action                        │
┌───────────────────────────────┐       │ parameters                    │
│     circuit_breaker_events    │       │ symbols                       │
├───────────────────────────────┤       │ exchanges                     │
│ id (PK)                       │       │ enabled                       │
│ circuit_breaker_id (FK)       │◄──────┤ created_at                    │
│ timestamp                     │       │ updated_at                    │
│ triggered_values              │       └───────────────────────────────┘
│ action_taken                  │       
│ action_result                 │       
│ positions_affected            │       
└───────────────────────────────┘       
```

## Usage Examples

### Loading a Risk Configuration

```python
from data.database import get_db
from data.repositories import RiskConfigurationRepository

# Get database session
db = next(get_db())

# Create repository
repo = RiskConfigurationRepository()

# Get configuration
config = repo.get_by_id(db, "default", "account123")

# Use the configuration
if config:
    print(f"Max position size: {config.max_position_size_percentage}%")
```

### Saving a Risk Configuration

```python
from data.database import get_db
from data.repositories import RiskConfigurationRepository

# Get database session
db = next(get_db())

# Create repository
repo = RiskConfigurationRepository()

# Create configuration data
config_data = {
    "config_id": "low_risk",
    "account_id": "account123",
    "position_max_drawdown_percentage": 3.0,
    "position_trailing_stop_multiplier": 1.5,
    "daily_max_drawdown_percentage": 2.0,
    "weekly_max_drawdown_percentage": 5.0,
    "monthly_max_drawdown_percentage": 10.0,
    "max_position_size_percentage": 5.0,
    "max_correlated_exposure_percentage": 10.0,
    "risk_per_trade_percentage": 0.5,
    "volatility_adjustment_factor": 0.8,
    "market_regime_thresholds": {},
    "cooling_off_period_minutes": 120,
    "consecutive_loss_threshold": 2,
    "is_active": True,
    "symbol_configs": [
        {
            "symbol": "BTCUSDT",
            "max_position_size_percentage": 3.0,
            "max_leverage": 5,
            "position_max_drawdown_percentage": 2.0,
            "risk_per_trade_percentage": 0.3
        }
    ]
}

# Create or update the configuration
config = repo.create(db, config_data)
```

### Managing Circuit Breakers

```python
from data.database import get_db
from data.repositories import CircuitBreakerRepository

# Get database session
db = next(get_db())

# Create repository
repo = CircuitBreakerRepository()

# Create circuit breaker data
breaker_data = {
    "name": "max_drawdown_10_percent",
    "description": "Close position when drawdown exceeds 10%",
    "account_id": "account123",
    "condition": "max_drawdown",
    "action": "close_position",
    "parameters": {"threshold": 0.1},
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "exchanges": ["binance"],
    "enabled": True
}

# Create the circuit breaker
breaker = repo.create(db, breaker_data)

# Enable/disable circuit breaker
repo.disable(db, breaker.id)
repo.enable(db, breaker.id)

# Log an event
event_data = {
    "circuit_breaker_id": breaker.id,
    "triggered_values": {"drawdown": 0.12},
    "action_taken": "close_position",
    "action_result": {"success": True},
    "positions_affected": [{"symbol": "BTCUSDT", "exchange": "binance"}]
}
repo.log_event(db, event_data)
``` 