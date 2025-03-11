# ETRMS Backtesting API Documentation

This document provides detailed information about the REST API endpoints for the ETRMS Backtesting Module. These endpoints allow you to run various backtesting analyses and retrieve results programmatically.

## Authentication

All API requests require authentication. Include your API key in the header of each request:

```
Authorization: Bearer YOUR_API_KEY
```

## Base URL

All endpoints are relative to the base URL:

```
https://your-etrms-instance.com/api
```

## Basic Backtesting

### Run a Backtest

Creates and runs a new backtest task based on the specified parameters.

**Endpoint**

```
POST /backtest
```

**Request Body**

```json
{
  "strategy_name": "MovingAverageCrossover",
  "symbols": ["BTC/USDT", "ETH/USDT"],
  "start_date": "2022-01-01",
  "end_date": "2022-12-31",
  "timeframe": "1h",
  "initial_balance": 10000,
  "fee_rate": 0.001,
  "slippage": 0.0005,
  "risk_per_trade": 0.02,
  "parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "signal_period": 9
  },
  "run_in_background": true
}
```

**Response**

```json
{
  "task_id": "bt_f8e7d6c5b4a3",
  "status": "pending",
  "created_at": "2023-05-15T14:30:22Z",
  "message": "Backtest task created successfully"
}
```

### Get Backtest Status

Retrieves the current status of a backtest task.

**Endpoint**

```
GET /backtest/status/{task_id}
```

**Parameters**

- `task_id` (path): The ID of the backtest task

**Response**

```json
{
  "task_id": "bt_f8e7d6c5b4a3",
  "status": "completed",
  "progress": 100,
  "created_at": "2023-05-15T14:30:22Z",
  "started_at": "2023-05-15T14:30:25Z",
  "completed_at": "2023-05-15T14:32:10Z"
}
```

### Get Backtest Results

Retrieves the results of a completed backtest.

**Endpoint**

```
GET /backtest/results/{task_id}
```

**Parameters**

- `task_id` (path): The ID of the backtest task

**Response**

```json
{
  "task_id": "bt_f8e7d6c5b4a3",
  "strategy_name": "MovingAverageCrossover",
  "symbols": ["BTC/USDT", "ETH/USDT"],
  "timeframe": "1h",
  "start_date": "2022-01-01",
  "end_date": "2022-12-31",
  "metrics": {
    "total_return": 28.45,
    "sharpe_ratio": 1.82,
    "max_drawdown": 15.3,
    "win_rate": 0.58,
    "profit_factor": 1.65,
    "total_trades": 124,
    "winning_trades": 72,
    "losing_trades": 52
  },
  "equity_curve": [
    {"timestamp": "2022-01-01T00:00:00Z", "equity": 10000},
    {"timestamp": "2022-01-01T01:00:00Z", "equity": 10025},
    // ... additional equity points
  ],
  "trades": [
    {
      "id": 1,
      "symbol": "BTC/USDT",
      "side": "buy",
      "entry_time": "2022-01-05T08:00:00Z",
      "entry_price": 46250.5,
      "exit_time": "2022-01-07T14:00:00Z",
      "exit_price": 47500.25,
      "quantity": 0.1,
      "profit_loss": 124.98,
      "profit_loss_percent": 2.7
    },
    // ... additional trades
  ]
}
```

## Monte Carlo Simulation

### Run Monte Carlo Simulation

Runs a Monte Carlo simulation on an existing backtest's trade history.

**Endpoint**

```
POST /backtest/monte-carlo/{task_id}
```

**Parameters**

- `task_id` (path): The ID of the backtest task

**Request Body**

```json
{
  "simulations": 1000,
  "random_seed": 42
}
```

**Response**

```json
{
  "task_id": "bt_f8e7d6c5b4a3",
  "monte_carlo_id": "mc_1a2b3c4d5e",
  "status": "processing",
  "message": "Monte Carlo simulation started"
}
```

### Get Monte Carlo Results

Retrieves the results of a completed Monte Carlo simulation.

**Endpoint**

```
GET /backtest/monte-carlo/results/{monte_carlo_id}
```

**Parameters**

- `monte_carlo_id` (path): The ID of the Monte Carlo simulation

**Response**

```json
{
  "monte_carlo_id": "mc_1a2b3c4d5e",
  "task_id": "bt_f8e7d6c5b4a3",
  "simulations": 1000,
  "summary": {
    "avg_final_balance": 12845.32,
    "median_final_balance": 12690.15,
    "min_final_balance": 9250.48,
    "max_final_balance": 17850.22,
    "std_dev_balance": 1250.45,
    "profit_probability": 0.92,
    "loss_probability": 0.08
  },
  "risk_metrics": {
    "var_95": 1500.25,
    "var_99": 2200.45,
    "cvar_95": 1850.35,
    "cvar_99": 2450.85,
    "max_drawdown_mean": 18.45,
    "max_drawdown_median": 17.8,
    "max_drawdown_worst": 32.6
  },
  "percentiles": {
    "final_balance": {
      "5": 10650.25,
      "25": 11750.45,
      "50": 12690.15,
      "75": 13950.30,
      "95": 15450.75
    }
  },
  "equity_curves": {
    "median": [
      {"timestamp": "2022-01-01T00:00:00Z", "equity": 10000},
      {"timestamp": "2022-01-01T01:00:00Z", "equity": 10015},
      // ... additional equity points
    ],
    "percentile_5": [...],
    "percentile_25": [...],
    "percentile_75": [...],
    "percentile_95": [...]
  }
}
```

## Parameter Optimization

### Run Parameter Optimization

Creates and runs a parameter optimization task to find the best parameters for a strategy.

**Endpoint**

```
POST /backtest/optimize
```

**Request Body**

```json
{
  "strategy_name": "MovingAverageCrossover",
  "parameter_grid": {
    "fast_period": [5, 10, 15, 20],
    "slow_period": [25, 30, 35, 40],
    "signal_period": [7, 8, 9, 10]
  },
  "symbols": ["BTC/USDT"],
  "start_date": "2022-01-01",
  "end_date": "2022-12-31",
  "timeframe": "1h",
  "initial_balance": 10000,
  "fee_rate": 0.001,
  "slippage": 0.0005,
  "risk_per_trade": 0.02,
  "optimization_metric": "sharpe_ratio",
  "run_in_background": true
}
```

**Response**

```json
{
  "task_id": "opt_a1b2c3d4e5",
  "status": "pending",
  "total_combinations": 64,
  "created_at": "2023-05-15T15:40:12Z",
  "message": "Parameter optimization task created successfully"
}
```

### Get Optimization Results

Retrieves the results of a completed parameter optimization task.

**Endpoint**

```
GET /backtest/optimize/results/{task_id}
```

**Parameters**

- `task_id` (path): The ID of the optimization task

**Response**

```json
{
  "task_id": "opt_a1b2c3d4e5",
  "strategy_name": "MovingAverageCrossover",
  "optimization_metric": "sharpe_ratio",
  "total_combinations": 64,
  "completed_combinations": 64,
  "best_parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "signal_period": 9
  },
  "best_metrics": {
    "sharpe_ratio": 2.15,
    "total_return": 35.25,
    "max_drawdown": 12.8,
    "win_rate": 0.62,
    "profit_factor": 1.85,
    "total_trades": 118
  },
  "parameter_analysis": {
    "fast_period": {
      "5": {"avg_metric": 1.65, "count": 16},
      "10": {"avg_metric": 2.05, "count": 16},
      "15": {"avg_metric": 1.85, "count": 16},
      "20": {"avg_metric": 1.55, "count": 16}
    },
    "slow_period": {
      "25": {"avg_metric": 1.75, "count": 16},
      "30": {"avg_metric": 1.95, "count": 16},
      "35": {"avg_metric": 1.85, "count": 16},
      "40": {"avg_metric": 1.55, "count": 16}
    },
    "signal_period": {
      "7": {"avg_metric": 1.65, "count": 16},
      "8": {"avg_metric": 1.85, "count": 16},
      "9": {"avg_metric": 2.05, "count": 16},
      "10": {"avg_metric": 1.55, "count": 16}
    }
  },
  "top_results": [
    {
      "parameters": {
        "fast_period": 10,
        "slow_period": 30,
        "signal_period": 9
      },
      "metrics": {
        "sharpe_ratio": 2.15,
        "total_return": 35.25,
        "max_drawdown": 12.8
      },
      "rank": 1
    },
    {
      "parameters": {
        "fast_period": 10,
        "slow_period": 30,
        "signal_period": 8
      },
      "metrics": {
        "sharpe_ratio": 2.05,
        "total_return": 33.15,
        "max_drawdown": 13.2
      },
      "rank": 2
    },
    // ... additional top results
  ]
}
```

## Walk-Forward Analysis

### Run Walk-Forward Analysis

Creates and runs a walk-forward analysis task to validate strategy robustness.

**Endpoint**

```
POST /backtest/walk-forward
```

**Request Body**

```json
{
  "strategy_name": "MovingAverageCrossover",
  "parameter_grid": {
    "fast_period": [5, 10, 15, 20],
    "slow_period": [25, 30, 35, 40],
    "signal_period": [7, 8, 9, 10]
  },
  "symbols": ["BTC/USDT"],
  "start_date": "2022-01-01",
  "end_date": "2022-12-31",
  "timeframe": "1h",
  "initial_balance": 10000,
  "fee_rate": 0.001,
  "slippage": 0.0005,
  "risk_per_trade": 0.02,
  "optimization_metric": "sharpe_ratio",
  "window_size_days": 90,
  "step_size_days": 30,
  "in_sample_pct": 0.7,
  "run_in_background": true
}
```

**Response**

```json
{
  "task_id": "wf_5e4d3c2b1a",
  "status": "pending",
  "created_at": "2023-05-15T16:20:45Z",
  "message": "Walk-forward analysis task created successfully"
}
```

### Get Walk-Forward Results

Retrieves the results of a completed walk-forward analysis.

**Endpoint**

```
GET /backtest/walk-forward/results/{task_id}
```

**Parameters**

- `task_id` (path): The ID of the walk-forward analysis task

**Response**

```json
{
  "task_id": "wf_5e4d3c2b1a",
  "strategy_name": "MovingAverageCrossover",
  "symbols": ["BTC/USDT"],
  "timeframe": "1h",
  "start_date": "2022-01-01",
  "end_date": "2022-12-31",
  "window_count": 12,
  "combined_metrics": {
    "total_return": 25.85,
    "sharpe_ratio": 1.75,
    "max_drawdown": 14.8,
    "win_rate": 0.56,
    "profit_factor": 1.55,
    "total_trades": 98
  },
  "windows": [
    {
      "window_id": 1,
      "in_sample_start": "2022-01-01",
      "in_sample_end": "2022-03-31",
      "out_sample_start": "2022-04-01",
      "out_sample_end": "2022-04-30",
      "optimized_parameters": {
        "fast_period": 10,
        "slow_period": 30,
        "signal_period": 9
      },
      "in_sample_metrics": {
        "sharpe_ratio": 2.15,
        "total_return": 12.25,
        "max_drawdown": 8.8
      },
      "out_sample_metrics": {
        "sharpe_ratio": 1.85,
        "total_return": 5.35,
        "max_drawdown": 4.2
      }
    },
    // ... additional windows
  ],
  "parameter_evolution": {
    "fast_period": [10, 15, 10, 15, 10, 15, 10, 10, 5, 10, 10, 10],
    "slow_period": [30, 30, 35, 30, 30, 30, 35, 30, 30, 30, 30, 35],
    "signal_period": [9, 8, 9, 9, 8, 9, 9, 8, 9, 8, 9, 9]
  },
  "window_performance": {
    "in_sample_returns": [12.25, 10.15, 11.5, 9.8, 8.7, 10.2, 11.5, 12.4, 9.8, 10.5, 11.2, 9.6],
    "out_sample_returns": [5.35, 3.85, 4.2, 3.1, 2.8, 3.5, 4.2, 3.8, 3.0, 3.6, 3.9, 3.2]
  }
}
```

## Error Responses

### Standard Error Response

```json
{
  "error": true,
  "code": 400,
  "message": "Invalid request parameters",
  "details": "Parameter 'strategy_name' is required"
}
```

### Common Error Codes

- `400` - Bad Request: Invalid parameters or request format
- `401` - Unauthorized: Missing or invalid API key
- `403` - Forbidden: Insufficient permissions
- `404` - Not Found: Resource not found
- `409` - Conflict: Resource already exists or operation cannot be completed
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Unexpected server error

## Rate Limiting

API requests are subject to rate limiting to ensure system stability. Current limits:

- 60 requests per minute per API key
- 1000 requests per day per API key

Rate limit headers are included in each response:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1621025400
```

## Pagination

For endpoints that return large collections of data, pagination is supported using the following query parameters:

- `page`: Page number (starting at 1)
- `limit`: Number of items per page (default: 20, max: 100)

Example:

```
GET /backtest/results?page=2&limit=50
```

Pagination metadata is included in the response:

```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "page": 2,
    "limit": 50,
    "pages": 3
  }
}
``` 