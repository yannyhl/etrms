-- Enhanced Trading Risk Management System Database Schema

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Positions Table
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    position_id VARCHAR(50) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    size DECIMAL(20, 8) NOT NULL,
    leverage INT NOT NULL,
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8),
    unrealized_pnl_percentage DECIMAL(10, 2),
    creation_time TIMESTAMP NOT NULL,
    last_update_time TIMESTAMP NOT NULL,
    status VARCHAR(10) NOT NULL,
    UNIQUE(exchange, position_id)
);

CREATE INDEX idx_positions_account_id ON positions(account_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_status ON positions(status);

-- Accounts Table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    total_equity DECIMAL(20, 8) NOT NULL,
    available_balance DECIMAL(20, 8) NOT NULL,
    margin_balance DECIMAL(20, 8) NOT NULL,
    open_position_count INT NOT NULL,
    daily_pnl DECIMAL(20, 8) NOT NULL,
    daily_pnl_percentage DECIMAL(10, 2) NOT NULL,
    weekly_pnl DECIMAL(20, 8) NOT NULL,
    weekly_pnl_percentage DECIMAL(10, 2) NOT NULL,
    monthly_pnl DECIMAL(20, 8) NOT NULL,
    monthly_pnl_percentage DECIMAL(10, 2) NOT NULL,
    peak_equity DECIMAL(20, 8) NOT NULL,
    current_drawdown_percentage DECIMAL(10, 2) NOT NULL,
    last_update_time TIMESTAMP NOT NULL,
    UNIQUE(exchange, account_id)
);

-- Risk Configuration Table
CREATE TABLE risk_configurations (
    id SERIAL PRIMARY KEY,
    config_id VARCHAR(50) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    position_max_drawdown_percentage DECIMAL(10, 2) NOT NULL,
    position_trailing_stop_multiplier DECIMAL(10, 2) NOT NULL,
    daily_max_drawdown_percentage DECIMAL(10, 2) NOT NULL,
    weekly_max_drawdown_percentage DECIMAL(10, 2) NOT NULL,
    monthly_max_drawdown_percentage DECIMAL(10, 2) NOT NULL,
    max_position_size_percentage DECIMAL(10, 2) NOT NULL,
    max_correlated_exposure_percentage DECIMAL(10, 2) NOT NULL,
    risk_per_trade_percentage DECIMAL(10, 2) NOT NULL,
    volatility_adjustment_factor DECIMAL(10, 2) NOT NULL,
    market_regime_thresholds JSONB NOT NULL,
    cooling_off_period_minutes INT NOT NULL,
    consecutive_loss_threshold INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    UNIQUE(account_id, config_id)
);

-- Trades Table
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8) NOT NULL,
    size DECIMAL(20, 8) NOT NULL,
    pnl DECIMAL(20, 8) NOT NULL,
    pnl_percentage DECIMAL(10, 2) NOT NULL,
    fees DECIMAL(20, 8) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP NOT NULL,
    duration_minutes INT NOT NULL,
    setup_type VARCHAR(50),
    market_regime JSONB,
    risk_reward_planned DECIMAL(10, 2),
    initial_stop_loss DECIMAL(20, 8),
    initial_take_profit DECIMAL(20, 8),
    exit_reason VARCHAR(50) NOT NULL,
    UNIQUE(exchange, trade_id)
);

CREATE INDEX idx_trades_account_id ON trades(account_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);

-- Market Regimes Table
CREATE TABLE market_regimes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    trend_status VARCHAR(20) NOT NULL,
    volatility_regime VARCHAR(10) NOT NULL,
    mean_reversion_probability DECIMAL(10, 2) NOT NULL,
    current_volatility DECIMAL(10, 2) NOT NULL,
    historical_volatility_percentile DECIMAL(10, 2) NOT NULL,
    adx_value DECIMAL(10, 2) NOT NULL,
    correlation_matrix JSONB NOT NULL,
    liquidity_score DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE(symbol, timeframe, created_at)
);

CREATE INDEX idx_market_regimes_symbol ON market_regimes(symbol);
CREATE INDEX idx_market_regimes_timeframe ON market_regimes(timeframe);
CREATE INDEX idx_market_regimes_created_at ON market_regimes(created_at);

-- Convert Market Regimes Table to a TimescaleDB hypertable
SELECT create_hypertable('market_regimes', 'created_at');

-- Users Table (for authentication)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- API Keys Table (for exchange access)
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    exchange VARCHAR(20) NOT NULL,
    api_key VARCHAR(100) NOT NULL,
    api_secret VARCHAR(100) NOT NULL,
    is_testnet BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    UNIQUE(user_id, exchange)
);

-- Circuit Breakers Table
CREATE TABLE circuit_breakers (
    id SERIAL PRIMARY KEY,
    config_id VARCHAR(50) REFERENCES risk_configurations(config_id),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    threshold DECIMAL(10, 2) NOT NULL,
    action VARCHAR(50) NOT NULL,
    cooldown_minutes INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Circuit Breaker Events Table
CREATE TABLE circuit_breaker_events (
    id SERIAL PRIMARY KEY,
    breaker_id INTEGER REFERENCES circuit_breakers(id),
    account_id VARCHAR(50) NOT NULL,
    position_id VARCHAR(50),
    triggered_value DECIMAL(20, 8) NOT NULL,
    threshold DECIMAL(20, 8) NOT NULL,
    action_taken VARCHAR(50) NOT NULL,
    result_summary TEXT,
    triggered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

SELECT create_hypertable('circuit_breaker_events', 'triggered_at'); 