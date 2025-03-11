# Enhanced Trading Risk Management System (ETRMS) API Documentation

This document provides comprehensive documentation for the ETRMS API, including both REST endpoints and WebSocket interfaces.

## General Information

- Base URL: `/api/v1`
- All responses follow a standard format:
  ```json
  {
    "status": "success|error",
    "message": "Description of the result",
    "data": { ... } // The actual data or null in case of error
  }
  ```

## Authentication

*Note: Authentication details to be implemented*

## REST API Endpoints

### Account API

#### Get Account Summary

- **URL**: `/accounts/`
- **Method**: `GET`
- **Description**: Retrieves a summary of account information across all exchanges.
- **Response**: Account summary information.

#### Get Exchange Account

- **URL**: `/accounts/{exchange}`
- **Method**: `GET`
- **Description**: Retrieves account information for a specific exchange.
- **Parameters**:
  - `exchange` (path): Exchange name (e.g., 'binance', 'hyperliquid')
- **Response**: Account information for the specified exchange.

#### Start Monitoring

- **URL**: `/accounts/monitor/start`
- **Method**: `POST`
- **Description**: Starts monitoring accounts and positions.
- **Parameters**:
  - `exchanges` (query, optional): List of exchanges to monitor
  - `symbols` (query, optional): List of symbols to monitor
- **Response**: Status of the monitoring start operation.

#### Stop Monitoring

- **URL**: `/accounts/monitor/stop`
- **Method**: `POST`
- **Description**: Stops monitoring accounts and positions.
- **Response**: Status of the monitoring stop operation.

#### Get Monitoring Status

- **URL**: `/accounts/monitor/status`
- **Method**: `GET`
- **Description**: Gets the current status of account and position monitoring.
- **Response**: Monitoring status information.

### Position API

#### Get Position Summary

- **URL**: `/positions/`
- **Method**: `GET`
- **Description**: Retrieves a summary of positions across all exchanges.
- **Response**: Position summary information.

#### Get Positions By Symbol

- **URL**: `/positions/by-symbol`
- **Method**: `GET`
- **Description**: Retrieves positions grouped by symbol across all exchanges.
- **Response**: Positions grouped by symbol.

#### Get Positions By Exchange

- **URL**: `/positions/by-exchange`
- **Method**: `GET`
- **Description**: Retrieves positions grouped by exchange.
- **Response**: Positions grouped by exchange.

#### Get Exchange Positions

- **URL**: `/positions/{exchange}`
- **Method**: `GET`
- **Description**: Retrieves positions for a specific exchange.
- **Parameters**:
  - `exchange` (path): Exchange name (e.g., 'binance', 'hyperliquid')
- **Response**: Positions for the specified exchange.

#### Get Specific Position

- **URL**: `/positions/{exchange}/{symbol}`
- **Method**: `GET`
- **Description**: Retrieves a specific position by exchange and symbol.
- **Parameters**:
  - `exchange` (path): Exchange name (e.g., 'binance', 'hyperliquid')
  - `symbol` (path): Symbol (e.g., 'BTCUSDT')
- **Response**: Position information.

### Risk API

#### Get Circuit Breakers

- **URL**: `/risk/circuit-breakers`
- **Method**: `GET`
- **Description**: Retrieves all circuit breaker conditions.
- **Response**: List of circuit breaker conditions.

#### Add Circuit Breaker

- **URL**: `/risk/circuit-breakers`
- **Method**: `POST`
- **Description**: Adds a new circuit breaker condition.
- **Parameters**:
  - `name` (body): Unique name for the condition
  - `description` (body): Description of the condition
  - `condition_type` (body): Type of condition (max_drawdown, max_position_size, pnl, trailing_stop, consecutive_losses, time_based, volatility)
  - `threshold` (body): Threshold value
  - `action` (body): Action to take (close_position, cancel_all_orders, reduce_position_size)
  - `symbols` (body, optional): Symbols this condition applies to (None for all)
  - `exchanges` (body, optional): Exchanges this condition applies to (None for all)
  - `enabled` (body, optional): Whether the condition is enabled
  - `additional_params` (body, optional): Additional parameters for specific condition types
- **Response**: Status of the add operation.

#### Remove Circuit Breaker

- **URL**: `/risk/circuit-breakers/{name}`
- **Method**: `DELETE`
- **Description**: Removes a circuit breaker condition.
- **Parameters**:
  - `name` (path): Name of the condition to remove
- **Response**: Status of the remove operation.

#### Enable Circuit Breaker

- **URL**: `/risk/circuit-breakers/{name}/enable`
- **Method**: `PUT`
- **Description**: Enables a circuit breaker condition.
- **Parameters**:
  - `name` (path): Name of the condition to enable
- **Response**: Status of the enable operation.

#### Disable Circuit Breaker

- **URL**: `/risk/circuit-breakers/{name}/disable`
- **Method**: `PUT`
- **Description**: Disables a circuit breaker condition.
- **Parameters**:
  - `name` (path): Name of the condition to disable
- **Response**: Status of the disable operation.

#### Evaluate Circuit Breakers

- **URL**: `/risk/evaluate`
- **Method**: `POST`
- **Description**: Manually evaluates circuit breaker conditions.
- **Response**: Evaluation results.

### Configuration API

#### Get All Config

- **URL**: `/config/`
- **Method**: `GET`
- **Description**: Retrieves all risk configuration settings.
- **Response**: All risk configuration settings.

#### Get Global Config

- **URL**: `/config/global`
- **Method**: `GET`
- **Description**: Retrieves global risk configuration settings.
- **Response**: Global risk configuration settings.

#### Update Global Config

- **URL**: `/config/global`
- **Method**: `PUT`
- **Description**: Updates global risk configuration settings.
- **Parameters**:
  - `settings` (body): Global risk configuration settings to update
- **Response**: Updated global risk configuration settings.

#### Get All Symbol Configs

- **URL**: `/config/symbols`
- **Method**: `GET`
- **Description**: Retrieves all symbol-specific risk configuration settings.
- **Response**: All symbol-specific risk configuration settings.

#### Get Symbol Config

- **URL**: `/config/symbols/{symbol}`
- **Method**: `GET`
- **Description**: Retrieves risk configuration settings for a specific symbol.
- **Parameters**:
  - `symbol` (path): Symbol (e.g., 'BTCUSDT')
- **Response**: Risk configuration settings for the specified symbol.

#### Update Symbol Config

- **URL**: `/config/symbols/{symbol}`
- **Method**: `PUT`
- **Description**: Updates risk configuration settings for a specific symbol.
- **Parameters**:
  - `symbol` (path): Symbol (e.g., 'BTCUSDT')
  - `settings` (body): Symbol-specific risk configuration settings to update
- **Response**: Updated risk configuration settings for the specified symbol.

#### Get All Exchange Configs

- **URL**: `/config/exchanges`
- **Method**: `GET`
- **Description**: Retrieves all exchange-specific risk configuration settings.
- **Response**: All exchange-specific risk configuration settings.

#### Get Exchange Config

- **URL**: `/config/exchanges/{exchange}`
- **Method**: `GET`
- **Description**: Retrieves risk configuration settings for a specific exchange.
- **Parameters**:
  - `exchange` (path): Exchange name (e.g., 'binance', 'hyperliquid')
- **Response**: Risk configuration settings for the specified exchange.

#### Update Exchange Config

- **URL**: `/config/exchanges/{exchange}`
- **Method**: `PUT`
- **Description**: Updates risk configuration settings for a specific exchange.
- **Parameters**:
  - `exchange` (path): Exchange name (e.g., 'binance', 'hyperliquid')
  - `settings` (body): Exchange-specific risk configuration settings to update
- **Response**: Updated risk configuration settings for the specified exchange.

#### Get Circuit Breaker Configs

- **URL**: `/config/circuit-breakers`
- **Method**: `GET`
- **Description**: Retrieves circuit breaker configurations.
- **Response**: Circuit breaker configurations.

#### Add Circuit Breaker Config

- **URL**: `/config/circuit-breakers`
- **Method**: `POST`
- **Description**: Adds a circuit breaker configuration.
- **Parameters**:
  - `circuit_breaker` (body): Circuit breaker configuration to add
- **Response**: Status of the add operation.

#### Update Circuit Breaker Config

- **URL**: `/config/circuit-breakers/{name}`
- **Method**: `PUT`
- **Description**: Updates a circuit breaker configuration.
- **Parameters**:
  - `name` (path): Name of the circuit breaker to update
  - `updates` (body): Updates to apply to the circuit breaker
- **Response**: Status of the update operation.

#### Remove Circuit Breaker Config

- **URL**: `/config/circuit-breakers/{name}`
- **Method**: `DELETE`
- **Description**: Removes a circuit breaker configuration.
- **Parameters**:
  - `name` (path): Name of the circuit breaker to remove
- **Response**: Status of the remove operation.

#### Save Config

- **URL**: `/config/save`
- **Method**: `POST`
- **Description**: Saves the current configuration to a file.
- **Parameters**:
  - `config_path` (body, optional): Path where to save the configuration
- **Response**: Status of the save operation.

#### Reset Config

- **URL**: `/config/reset`
- **Method**: `POST`
- **Description**: Resets configuration to default values.
- **Response**: Status of the reset operation.

## WebSocket API

The ETRMS provides WebSocket endpoints for real-time updates on accounts, positions, risk metrics, and alerts.

### Base URL

- WebSocket Base URL: `/api/v1/ws`

### Available Channels

#### Positions Channel

- **Endpoint**: `/ws/positions`
- **Description**: Real-time position updates
- **Message Format**:
  ```json
  {
    "total_position_value": 1234.56,
    "total_unrealized_pnl": 123.45,
    "exchanges": { 
      "exchange1": {
        "total_position_value": 1000.0,
        "total_unrealized_pnl": 100.0,
        "positions": [...]
      }
    },
    "positions_by_symbol": {...}
  }
  ```

#### Accounts Channel

- **Endpoint**: `/ws/accounts`
- **Description**: Real-time account updates
- **Message Format**:
  ```json
  {
    "accounts": {
      "exchange1": {
        "balance": 1000.0,
        "equity": 1100.0,
        "available": 900.0,
        "margin_used": 100.0
      },
      "exchange2": {...}
    }
  }
  ```

#### Risk Metrics Channel

- **Endpoint**: `/ws/risk-metrics`
- **Description**: Real-time risk metrics updates
- **Message Format**:
  ```json
  {
    "risk_metrics": {
      "total_exposure": 1000.0,
      "max_drawdown": 10.5,
      "total_pnl": 123.45,
      "exchange_metrics": {...},
      "symbol_metrics": {...}
    }
  }
  ```

#### Alerts Channel

- **Endpoint**: `/ws/alerts`
- **Description**: Real-time alerts when circuit breakers are triggered
- **Message Format**:
  ```json
  {
    "type": "circuit_breaker",
    "condition_name": "max_drawdown_exceeded",
    "description": "Position has exceeded maximum allowed drawdown",
    "exchange": "binance",
    "symbol": "BTCUSDT",
    "triggered_at": 1618346400,
    "context": {
      "current_drawdown": 15.5,
      "threshold": 10.0
    },
    "action_result": "Position closed successfully"
  }
  ```

### Using WebSockets

1. Connect to the WebSocket endpoint
2. Send a message (any text) to keep the connection alive
3. Receive real-time updates

Example (JavaScript):
```javascript
const ws = new WebSocket('wss://your-domain.com/api/v1/ws/positions');

ws.onopen = () => {
  console.log('Connected to positions WebSocket');
  // Send a message to keep the connection alive
  ws.send('subscribe');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received position update:', data);
};

ws.onclose = () => {
  console.log('Disconnected from positions WebSocket');
};
```

## Error Handling

All API endpoints follow a standardized error response format:

```json
{
  "status": "error",
  "message": "Description of the error",
  "data": null
}
```

Common HTTP status codes:
- `200 OK`: Successful request
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Not permitted to access resource
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error 