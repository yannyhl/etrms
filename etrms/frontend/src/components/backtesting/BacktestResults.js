import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ArrowPathIcon, 
  ExclamationCircleIcon, 
  ArrowDownIcon, 
  ArrowUpIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

function BacktestResults({ selectedTask }) {
  const [results, setResults] = useState(null);
  const [trades, setTrades] = useState([]);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [isLoadingTrades, setIsLoadingTrades] = useState(false);
  const [error, setError] = useState(null);
  const [activeMetricTab, setActiveMetricTab] = useState('performance');

  useEffect(() => {
    if (selectedTask && selectedTask.id) {
      fetchResults(selectedTask.id);
      fetchTrades(selectedTask.id);
    } else {
      setResults(null);
      setTrades([]);
    }
  }, [selectedTask]);

  const fetchResults = async (taskId) => {
    setIsLoadingResults(true);
    setError(null);
    
    try {
      const response = await axios.get(`/api/v1/backtesting/results/${taskId}`);
      setResults(response.data);
    } catch (err) {
      console.error('Error fetching backtest results:', err);
      setError('Failed to load backtest results. Please try again later.');
    } finally {
      setIsLoadingResults(false);
    }
  };

  const fetchTrades = async (taskId) => {
    setIsLoadingTrades(true);
    try {
      const response = await axios.get(`/api/v1/backtesting/trades/${taskId}`);
      setTrades(response.data.trades || []);
    } catch (err) {
      console.error('Error fetching backtest trades:', err);
      // Not setting error here to avoid overriding a potential results error
    } finally {
      setIsLoadingTrades(false);
    }
  };

  const formatNumber = (value, decimals = 2, prefix = '') => {
    if (value === undefined || value === null) return 'N/A';
    return `${prefix}${Number(value).toFixed(decimals)}`;
  };

  const formatPercentage = (value, decimals = 2) => {
    if (value === undefined || value === null) return 'N/A';
    return `${Number(value * 100).toFixed(decimals)}%`;
  };

  const formatCurrency = (value, decimals = 2) => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const prepareChartData = () => {
    if (!results?.equity_curve) return [];
    
    return results.equity_curve.map(point => ({
      time: new Date(point[0]),
      equity: point[1],
      drawdown: point[2] * -1 // Convert to negative for visualization
    }));
  };

  const getMetricColor = (value, isHigherBetter = true) => {
    if (value === undefined || value === null) return 'text-gray-500';
    if (value === 0) return 'text-gray-500';
    return value > 0 === isHigherBetter ? 'text-green-600' : 'text-red-600';
  };

  const getMetricIcon = (value, isHigherBetter = true) => {
    if (value === undefined || value === null || value === 0) return null;
    
    const IconComponent = value > 0 === isHigherBetter ? ArrowUpIcon : ArrowDownIcon;
    const colorClass = value > 0 === isHigherBetter ? 'text-green-600' : 'text-red-600';
    
    return <IconComponent className={`h-4 w-4 ${colorClass} inline`} />;
  };

  if (!selectedTask) {
    return (
      <div className="flex items-center justify-center h-64 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <div className="text-gray-500">
          <InformationCircleIcon className="h-10 w-10 mx-auto mb-2" />
          <p>Select a task from the Tasks tab to view results</p>
        </div>
      </div>
    );
  }

  if (isLoadingResults) {
    return (
      <div className="flex justify-center items-center h-64">
        <ArrowPathIcon className="h-8 w-8 text-blue-500 animate-spin" />
        <span className="ml-2 text-gray-600">Loading results...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <ExclamationCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">{error}</h3>
          </div>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="text-center py-10 bg-gray-100 rounded-lg">
        <p className="text-gray-600">
          {selectedTask.status === 'completed' 
            ? 'No results available. Run the backtest to generate results.'
            : `Task status: ${selectedTask.status}. Run the backtest to generate results.`}
        </p>
        <button 
          className="mt-4 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          onClick={() => fetchResults(selectedTask.id)}
        >
          Refresh Results
        </button>
      </div>
    );
  }

  const chartData = prepareChartData();

  return (
    <div className="space-y-6">
      {/* Metrics Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Metrics">
          <button
            className={`
              border-transparent whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm
              ${activeMetricTab === 'performance' 
                ? 'border-blue-500 text-blue-600' 
                : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
            onClick={() => setActiveMetricTab('performance')}
          >
            Performance
          </button>
          <button
            className={`
              border-transparent whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm
              ${activeMetricTab === 'risk' 
                ? 'border-blue-500 text-blue-600' 
                : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
            onClick={() => setActiveMetricTab('risk')}
          >
            Risk Metrics
          </button>
          <button
            className={`
              border-transparent whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm
              ${activeMetricTab === 'trades' 
                ? 'border-blue-500 text-blue-600' 
                : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
            onClick={() => setActiveMetricTab('trades')}
          >
            Trades
          </button>
        </nav>
      </div>

      {/* Equity Chart */}
      <div className="bg-white p-4 rounded-lg shadow border">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Equity Curve</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{
                top: 10,
                right: 30,
                left: 0,
                bottom: 0,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                tickFormatter={(time) => new Date(time).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  name === 'equity' 
                    ? formatCurrency(value) 
                    : formatPercentage(value * -1)
                  , 
                  name === 'equity' ? 'Balance' : 'Drawdown'
                ]}
                labelFormatter={(time) => new Date(time).toLocaleString()}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="equity" 
                stroke="#3b82f6" 
                fill="#93c5fd" 
                activeDot={{ r: 8 }} 
                name="Balance"
                unit="$"
              />
              {results.max_drawdown > 0 && (
                <Area 
                  type="monotone" 
                  dataKey="drawdown" 
                  stroke="#ef4444" 
                  fill="#fca5a5" 
                  name="Drawdown" 
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Metrics */}
      {activeMetricTab === 'performance' && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Net Profit</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.net_profit)}`}>
              {formatCurrency(results.net_profit)}
              {getMetricIcon(results.net_profit)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Return</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.return_percentage)}`}>
              {formatPercentage(results.return_percentage)}
              {getMetricIcon(results.return_percentage)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Profit Factor</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.profit_factor)}`}>
              {formatNumber(results.profit_factor)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Win Rate</h3>
            <div className="mt-1 text-xl font-semibold text-gray-800">
              {formatPercentage(results.win_rate)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Final Balance</h3>
            <div className="mt-1 text-xl font-semibold text-gray-800">
              {formatCurrency(results.final_balance)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Total Trades</h3>
            <div className="mt-1 text-xl font-semibold text-gray-800">
              {results.total_trades}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Sharpe Ratio</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.sharpe_ratio)}`}>
              {formatNumber(results.sharpe_ratio)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Sortino Ratio</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.sortino_ratio)}`}>
              {formatNumber(results.sortino_ratio)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Annual Return</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.annual_return)}`}>
              {formatPercentage(results.annual_return)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Winning Trades</h3>
            <div className="mt-1 text-xl font-semibold text-gray-800">
              {results.winning_trades}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Losing Trades</h3>
            <div className="mt-1 text-xl font-semibold text-gray-800">
              {results.losing_trades}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Avg. Trade</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.average_profit_per_trade)}`}>
              {formatCurrency(results.average_profit_per_trade)}
            </div>
          </div>
        </div>
      )}

      {/* Risk Metrics */}
      {activeMetricTab === 'risk' && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Max Drawdown</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.max_drawdown, false)}`}>
              {formatPercentage(results.max_drawdown)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Average Drawdown</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.average_drawdown, false)}`}>
              {formatPercentage(results.average_drawdown)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Max Drawdown Duration</h3>
            <div className="mt-1 text-xl font-semibold text-gray-800">
              {results.max_drawdown_duration} days
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Recovery Factor</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.recovery_factor)}`}>
              {formatNumber(results.recovery_factor)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Risk-Reward Ratio</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.risk_reward_ratio)}`}>
              {formatNumber(results.risk_reward_ratio)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Volatility</h3>
            <div className="mt-1 text-xl font-semibold text-gray-800">
              {formatPercentage(results.volatility)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Calmar Ratio</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.calmar_ratio)}`}>
              {formatNumber(results.calmar_ratio)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Value at Risk (95%)</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.var_95, false)}`}>
              {formatPercentage(results.var_95)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Expected Shortfall (95%)</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.cvar_95, false)}`}>
              {formatPercentage(results.cvar_95)}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Max Consecutive Wins</h3>
            <div className="mt-1 text-xl font-semibold text-gray-800">
              {results.max_consecutive_wins}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Max Consecutive Losses</h3>
            <div className="mt-1 text-xl font-semibold text-gray-800">
              {results.max_consecutive_losses}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="text-sm font-medium text-gray-500">Expectancy</h3>
            <div className={`mt-1 text-xl font-semibold ${getMetricColor(results.expectancy)}`}>
              {formatCurrency(results.expectancy)}
            </div>
          </div>
        </div>
      )}

      {/* Trades Table */}
      {activeMetricTab === 'trades' && (
        <div className="overflow-x-auto">
          {isLoadingTrades ? (
            <div className="flex justify-center items-center py-10">
              <ArrowPathIcon className="h-6 w-6 text-blue-500 animate-spin mr-2" />
              <span>Loading trades...</span>
            </div>
          ) : trades.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              No trades available for this backtest.
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entry Time</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entry Price</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Exit Time</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Exit Price</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Profit/Loss</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {trades.map((trade, index) => (
                  <tr key={trade.id || index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{trade.symbol}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        trade.side === 'long' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {trade.side === 'long' ? 'Long' : 'Short'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(trade.entry_time)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatNumber(trade.entry_price)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(trade.exit_time)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatNumber(trade.exit_price)}</td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                      trade.pnl > 0 ? 'text-green-600' : trade.pnl < 0 ? 'text-red-600' : 'text-gray-500'
                    }`}>
                      {formatCurrency(trade.pnl)} ({formatPercentage(trade.pnl_percentage)})
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

export default BacktestResults; 