# API Documentation

## Overview

The Enhanced Trading Risk Management System (ETRMS) API provides endpoints for managing trading risk, analyzing markets, and delivering AI-powered trading assistance.

## API Base URL

- Development: `http://localhost:8000`
- Production: `https://api.your-domain.com`

## Authentication

The API uses JWT (JSON Web Token) for authentication. To access protected endpoints, you need to include the JWT token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Authenticate a user and get a token
- `POST /api/auth/refresh` - Refresh an expired token
- `POST /api/auth/logout` - Invalidate a token

### Risk Management

- `GET /api/risk/configurations` - Get risk configurations
- `POST /api/risk/configurations` - Create a new risk configuration
- `GET /api/risk/configurations/{config_id}` - Get a specific risk configuration
- `PUT /api/risk/configurations/{config_id}` - Update a risk configuration
- `DELETE /api/risk/configurations/{config_id}` - Delete a risk configuration
- `GET /api/risk/circuit-breakers` - Get configured circuit breakers
- `POST /api/risk/circuit-breakers` - Create a new circuit breaker
- `GET /api/risk/circuit-breakers/{breaker_id}` - Get a specific circuit breaker
- `PUT /api/risk/circuit-breakers/{breaker_id}` - Update a circuit breaker
- `DELETE /api/risk/circuit-breakers/{breaker_id}` - Delete a circuit breaker

### Market Analysis

- `GET /api/market/regimes/{symbol}` - Get market regime for a symbol
- `GET /api/market/volume-profile/{symbol}` - Get volume profile for a symbol
- `GET /api/market/liquidity/{symbol}` - Get liquidity analysis for a symbol
- `GET /api/market/order-book/{symbol}` - Get order book analysis for a symbol

### AI Trading Assistant

- `GET /api/assistant/setups` - Get identified trading setups
- `GET /api/assistant/recommendations` - Get trading recommendations
- `GET /api/assistant/performance` - Get performance analytics

### Exchange Integration

- `GET /api/exchange/accounts` - Get connected exchange accounts
- `GET /api/exchange/positions` - Get current positions
- `POST /api/exchange/orders` - Create a new order
- `GET /api/exchange/orders` - Get orders
- `DELETE /api/exchange/orders/{order_id}` - Cancel an order

## Error Handling

The API returns standard HTTP status codes and a JSON response with an error message:

```json
{
  "status": "error",
  "message": "Detailed error message",
  "code": "ERROR_CODE"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Rate limits are specified in the response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1620000000
```

## Versioning

The API is versioned using the URL path, e.g., `/api/v1/resource`. The current version is v1. 