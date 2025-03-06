-- Enhanced Trading Risk Management System
-- Migration: Add Backtesting Tables
-- Date: 2024-07-10

-- Create backtesting_tasks table
CREATE TABLE IF NOT EXISTS backtest_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    strategy_params JSONB,
    symbols JSONB NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date VARCHAR(10) NOT NULL,
    end_date VARCHAR(10) NOT NULL,
    initial_balance FLOAT NOT NULL,
    fee_rate FLOAT NOT NULL,
    slippage FLOAT NOT NULL,
    risk_per_trade FLOAT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create indexes for backtest_tasks
CREATE INDEX IF NOT EXISTS idx_backtest_tasks_task_id ON backtest_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_backtest_tasks_user_id ON backtest_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_tasks_status ON backtest_tasks(status);
CREATE INDEX IF NOT EXISTS idx_backtest_tasks_created_at ON backtest_tasks(created_at);

-- Create backtest_results table
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL REFERENCES backtest_tasks(task_id) ON DELETE CASCADE,
    total_return FLOAT NOT NULL,
    total_return_percentage FLOAT NOT NULL,
    annualized_return_percentage FLOAT NOT NULL,
    sharpe_ratio FLOAT NOT NULL,
    max_drawdown FLOAT NOT NULL,
    max_drawdown_percentage FLOAT NOT NULL,
    win_rate FLOAT NOT NULL,
    profit_factor FLOAT NOT NULL,
    avg_profit_per_trade FLOAT NOT NULL,
    avg_loss_per_trade FLOAT NOT NULL,
    avg_trade FLOAT NOT NULL,
    avg_winning_trade FLOAT NOT NULL,
    avg_losing_trade FLOAT NOT NULL,
    max_winning_trade FLOAT NOT NULL,
    max_losing_trade FLOAT NOT NULL,
    recovery_factor FLOAT,
    calmar_ratio FLOAT,
    volatility FLOAT NOT NULL,
    total_trades INT NOT NULL,
    winning_trades INT NOT NULL,
    losing_trades INT NOT NULL,
    break_even_trades INT,
    equity_history JSONB NOT NULL,
    drawdown_history JSONB,
    monthly_returns JSONB,
    report_path VARCHAR(255)
);

-- Create indexes for backtest_results
CREATE INDEX IF NOT EXISTS idx_backtest_results_task_id ON backtest_results(task_id);

-- Create backtest_trades table
CREATE TABLE IF NOT EXISTS backtest_trades (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL REFERENCES backtest_tasks(task_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price FLOAT NOT NULL,
    exit_price FLOAT NOT NULL,
    size FLOAT NOT NULL,
    pnl FLOAT NOT NULL,
    pnl_percentage FLOAT NOT NULL,
    fees FLOAT NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP NOT NULL,
    duration_minutes INT NOT NULL,
    setup_type VARCHAR(50),
    market_regime JSONB,
    risk_reward_planned FLOAT,
    initial_stop_loss FLOAT,
    initial_take_profit FLOAT,
    exit_reason VARCHAR(50) NOT NULL
);

-- Create indexes for backtest_trades
CREATE INDEX IF NOT EXISTS idx_backtest_trades_task_id ON backtest_trades(task_id);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_symbol ON backtest_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_entry_time ON backtest_trades(entry_time);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_exit_time ON backtest_trades(exit_time);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_pnl ON backtest_trades(pnl); 