import { useState, useEffect } from 'react';
import axios from 'axios';
import { PlusIcon, TrashIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import useWebSocket from '../hooks/useWebSocket';
import { Channels } from '../services/websocket';
import WebSocketStatus from '../components/WebSocketStatus';

// Risk condition types
const CONDITION_TYPES = [
  { id: 'max_drawdown', name: 'Maximum Drawdown', description: 'Trigger when drawdown exceeds a threshold' },
  { id: 'max_position_size', name: 'Maximum Position Size', description: 'Trigger when position size exceeds a threshold' },
  { id: 'pnl', name: 'Profit & Loss', description: 'Trigger when P&L falls below a threshold' },
  { id: 'trailing_stop', name: 'Trailing Stop', description: 'Trigger when price retraces from the peak by a percentage' },
  { id: 'consecutive_losses', name: 'Consecutive Losses', description: 'Trigger after a number of consecutive losing trades' },
  { id: 'time_based', name: 'Time-Based', description: 'Trigger when a position has been open for too long' },
  { id: 'volatility', name: 'Volatility', description: 'Trigger when volatility exceeds a threshold' }
];

// Action types
const ACTION_TYPES = [
  { id: 'close_position', name: 'Close Position', description: 'Close the position completely' },
  { id: 'cancel_all_orders', name: 'Cancel All Orders', description: 'Cancel all open orders for the symbol' },
  { id: 'reduce_position', name: 'Reduce Position', description: 'Reduce the position size by a percentage' }
];

export default function RiskManagement() {
  const [circuitBreakers, setCircuitBreakers] = useState([]);
  const [riskMetrics, setRiskMetrics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCondition, setNewCondition] = useState({
    name: '',
    description: '',
    condition_type: 'max_drawdown',
    threshold: 10,
    action: 'close_position',
    symbols: '',
    exchanges: '',
    enabled: true
  });
  const [expandedBreaker, setExpandedBreaker] = useState(null);
  const [activeTab, setActiveTab] = useState('circuit_breakers'); // 'circuit_breakers', 'risk_limits', 'risk_metrics'
  const [lastUpdated, setLastUpdated] = useState(null);

  // WebSocket connection for real-time risk metrics data
  const { 
    data: riskMetricsData, 
    status: riskMetricsStatus, 
    isConnected: isRiskMetricsConnected,
    connect: connectRiskMetricsWs,
    error: riskMetricsError
  } = useWebSocket(Channels.RISK_METRICS);

  // WebSocket connection for real-time alerts
  const { 
    data: alertsData, 
    status: alertsStatus, 
    isConnected: isAlertsConnected,
    connect: connectAlertsWs,
    error: alertsError
  } = useWebSocket(Channels.ALERTS);

  // Mock data for circuit breakers (used for development)
  const mockCircuitBreakers = [
    {
      name: "btc_drawdown_protection",
      description: "Close BTC position if drawdown exceeds 10%",
      condition_type: "max_drawdown",
      threshold: 10,
      action: "close_position",
      symbols: ["BTCUSDT"],
      exchanges: ["binance"],
      enabled: true
    },
    {
      name: "eth_drawdown_protection",
      description: "Close ETH position if drawdown exceeds 15%",
      condition_type: "max_drawdown",
      threshold: 15,
      action: "close_position",
      symbols: ["ETHUSDT"],
      exchanges: ["hyperliquid"],
      enabled: true
    },
    {
      name: "max_exposure_binance",
      description: "Cancel all orders when position size exceeds 1 BTC",
      condition_type: "max_position_size",
      threshold: 1,
      action: "cancel_all_orders",
      symbols: ["BTCUSDT"],
      exchanges: ["binance"],
      enabled: false
    },
    {
      name: "trailing_stop_btc",
      description: "Close BTC position if price retraces 5% from peak",
      condition_type: "trailing_stop",
      threshold: 5,
      action: "close_position",
      symbols: ["BTCUSDT"],
      exchanges: ["binance"],
      enabled: true
    }
  ];
  
  // Mock risk limits (used for development)
  const mockRiskLimits = {
    global: {
      max_total_exposure_usd: 100000.0,
      max_single_position_usd: 10000.0,
      max_leverage: 10.0,
      max_drawdown_percentage: 15.0
    },
    symbols: {
      "BTCUSDT": {
        max_position_size: 1.0,
        max_leverage: 5.0,
        max_drawdown_percentage: 10.0
      },
      "ETHUSDT": {
        max_position_size: 10.0,
        max_leverage: 4.0,
        max_drawdown_percentage: 12.0
      }
    },
    exchanges: {
      "binance": {
        max_total_exposure_usd: 50000.0,
      },
      "hyperliquid": {
        max_total_exposure_usd: 50000.0
      }
    }
  };

  // Mock risk metrics (used for development when API is not available)
  const mockRiskMetrics = {
    total_equity: 125000.0,
    total_position_value: 45000.0,
    largest_position: {
      value: 25000.0,
      symbol: "BTCUSDT",
      exchange: "binance"
    },
    highest_leverage: {
      leverage: 5.0,
      symbol: "ETHUSDT",
      exchange: "hyperliquid"
    },
    total_unrealized_pnl: 1500.0,
    total_unrealized_pnl_percentage: 3.33,
    drawdown: {
      daily: 1.2,
      weekly: 2.5,
      monthly: 4.8
    },
    exposure_percentage: 36.0,
    positions_by_exchange: {
      "binance": {
        position_count: 1,
        position_value: 25000.0,
        unrealized_pnl: 1000.0,
        exposure_percentage: 33.3
      },
      "hyperliquid": {
        position_count: 1,
        position_value: 20000.0,
        unrealized_pnl: 500.0,
        exposure_percentage: 40.0
      }
    },
    position_count: 2
  };

  // Update risk metrics when received from WebSocket
  useEffect(() => {
    if (riskMetricsData) {
      // Set last updated timestamp
      setLastUpdated(new Date());
      
      let metricsData;
      
      // Process the data structure from WebSocket
      if (riskMetricsData.risk_metrics) {
        // Format from WebSocket endpoint
        metricsData = riskMetricsData.risk_metrics;
      } else if (riskMetricsData.data && riskMetricsData.data.risk_metrics) {
        // Format from API response wrapped in data field
        metricsData = riskMetricsData.data.risk_metrics;
      } else if (riskMetricsData.data) {
        // Format directly from API response
        metricsData = riskMetricsData.data;
      } else {
        // Direct format
        metricsData = riskMetricsData;
      }
      
      // Update risk metrics state
      setRiskMetrics(metricsData);

      // If circuit breakers are included in the update, set them too
      let breakersData = null;
      if (riskMetricsData.circuit_breakers) {
        breakersData = riskMetricsData.circuit_breakers;
      } else if (riskMetricsData.data && riskMetricsData.data.circuit_breakers) {
        breakersData = riskMetricsData.data.circuit_breakers;
      }
      
      if (breakersData) {
        setCircuitBreakers(breakersData);
      }
      
      setLoading(false);
    }
  }, [riskMetricsData]);

  // Handle circuit breaker alerts from WebSocket
  useEffect(() => {
    if (alertsData && alertsData.type === 'circuit_breaker_triggered') {
      // Set last updated timestamp
      setLastUpdated(new Date());
      
      // Show an alert or notification when a circuit breaker is triggered
      const alert = alertsData.data || alertsData;
      
      // Update the local circuit breakers state to reflect the triggered condition
      setCircuitBreakers(prevBreakers => {
        return prevBreakers.map(breaker => {
          if (breaker.name === alert.condition_name) {
            return { ...breaker, last_triggered: alert.timestamp, triggered_count: (breaker.triggered_count || 0) + 1 };
          }
          return breaker;
        });
      });
      
      // You could also display a toast notification here
      console.log('Circuit breaker triggered:', alert);
    }
  }, [alertsData]);

  // Fetch circuit breakers data initially or when WebSocket is not connected
  useEffect(() => {
    if (!isRiskMetricsConnected) {
      fetchCircuitBreakers();
      fetchRiskMetrics();
    }
  }, [isRiskMetricsConnected]);

  // Fetch circuit breakers data
  const fetchCircuitBreakers = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/risk/circuit-breakers');
      if (response.data.status === 'success' && response.data.data) {
        setCircuitBreakers(response.data.data.conditions || []);
      } else {
        // Using mock data for development
        setCircuitBreakers(mockCircuitBreakers);
      }
      setLoading(false);
    } catch (err) {
      console.error('Error fetching circuit breakers:', err);
      setError('Failed to fetch circuit breakers. Please try again.');
      
      // Using mock data for development
      setCircuitBreakers(mockCircuitBreakers);
      setLoading(false);
    }
  };

  // Fetch risk metrics data
  const fetchRiskMetrics = async () => {
    try {
      const response = await axios.get('/api/v1/risk/metrics');
      if (response.data.status === 'success' && response.data.data) {
        setRiskMetrics(response.data.data);
      } else {
        // Using mock data for development
        setRiskMetrics(mockRiskMetrics);
      }
      
      // Set last updated timestamp
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching risk metrics:', err);
      // Using mock data for development
      setRiskMetrics(mockRiskMetrics);
      
      // Set last updated timestamp
      setLastUpdated(new Date());
    }
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (type === 'checkbox') {
      setNewCondition(prev => ({ ...prev, [name]: checked }));
    } else if (name === 'symbols' || name === 'exchanges') {
      // Handle comma-separated inputs for arrays
      setNewCondition(prev => ({ 
        ...prev, 
        [name]: value.split(',').map(item => item.trim()).filter(Boolean)
      }));
    } else if (name === 'threshold') {
      // Convert threshold to number
      setNewCondition(prev => ({ ...prev, [name]: parseFloat(value) }));
    } else {
      setNewCondition(prev => ({ ...prev, [name]: value }));
    }
  };

  // Handle adding a new circuit breaker
  const handleAddCircuitBreaker = async (e) => {
    e.preventDefault();
    
    try {
      // In a real app, this would be an API call
      // const response = await axios.post('/api/risk/circuit-breakers', newCondition);
      
      // Using mock response for now
      const newBreaker = { ...newCondition };
      
      setCircuitBreakers(prev => [...prev, newBreaker]);
      setShowAddForm(false);
      setNewCondition({
        name: '',
        description: '',
        condition_type: 'max_drawdown',
        threshold: 10,
        action: 'close_position',
        symbols: '',
        exchanges: '',
        enabled: true
      });
    } catch (err) {
      console.error('Error adding circuit breaker:', err);
      setError('Failed to add circuit breaker. Please try again.');
    }
  };

  // Handle enabling/disabling a circuit breaker
  const handleToggleEnabled = async (name, enabled) => {
    try {
      // In a real app, this would be an API call
      // await axios.put(`/api/risk/circuit-breakers/${name}/${enabled ? 'enable' : 'disable'}`);
      
      // Update local state
      setCircuitBreakers(prev => prev.map(breaker => 
        breaker.name === name ? { ...breaker, enabled: !breaker.enabled } : breaker
      ));
    } catch (err) {
      console.error('Error toggling circuit breaker:', err);
      setError(`Failed to ${enabled ? 'disable' : 'enable'} circuit breaker. Please try again.`);
    }
  };

  // Handle removing a circuit breaker
  const handleRemoveCircuitBreaker = async (name) => {
    if (!window.confirm(`Are you sure you want to delete the circuit breaker "${name}"?`)) {
      return;
    }
    
    try {
      // In a real app, this would be an API call
      // await axios.delete(`/api/risk/circuit-breakers/${name}`);
      
      // Update local state
      setCircuitBreakers(prev => prev.filter(breaker => breaker.name !== name));
    } catch (err) {
      console.error('Error removing circuit breaker:', err);
      setError('Failed to remove circuit breaker. Please try again.');
    }
  };

  // Toggle expanded breaker
  const toggleExpand = (name) => {
    setExpandedBreaker(expandedBreaker === name ? null : name);
  };

  // Render the circuit breakers tab
  const renderCircuitBreakers = () => {
    return (
      <div className="space-y-6">
        {/* List of circuit breakers */}
        <div className="space-y-4">
          {circuitBreakers.map((breaker) => (
            <div 
              key={breaker.name} 
              className={`card transition-all duration-200 ${
                expandedBreaker === breaker.name ? 'border-primary-300 shadow-md' : 'border border-secondary-200'
              }`}
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <button
                    onClick={() => toggleExpand(breaker.name)}
                    className="mr-2 text-secondary-500 hover:text-secondary-700"
                  >
                    {expandedBreaker === breaker.name ? (
                      <ChevronUpIcon className="h-5 w-5" />
                    ) : (
                      <ChevronDownIcon className="h-5 w-5" />
                    )}
                  </button>
                  <div>
                    <h3 className="font-semibold">{breaker.name}</h3>
                    <p className="text-sm text-secondary-500">{breaker.description}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="flex items-center">
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer"
                        checked={breaker.enabled}
                        onChange={() => handleToggleEnabled(breaker.name, breaker.enabled)}
                      />
                      <div className="w-9 h-5 bg-secondary-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-secondary-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                  <button
                    onClick={() => handleRemoveCircuitBreaker(breaker.name)}
                    className="text-secondary-500 hover:text-danger-500"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
              
              {expandedBreaker === breaker.name && (
                <div className="mt-4 pt-4 border-t border-secondary-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-secondary-500">Condition Type</p>
                      <p className="font-medium">
                        {CONDITION_TYPES.find(c => c.id === breaker.condition_type)?.name || breaker.condition_type}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-secondary-500">Threshold</p>
                      <p className="font-medium">
                        {breaker.threshold}
                        {breaker.condition_type === 'max_drawdown' && '%'}
                        {breaker.condition_type === 'max_position_size' && ' BTC'}
                        {breaker.condition_type === 'pnl' && '%'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-secondary-500">Action</p>
                      <p className="font-medium">
                        {ACTION_TYPES.find(a => a.id === breaker.action)?.name || breaker.action}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-secondary-500">Status</p>
                      <p className={`font-medium ${breaker.enabled ? 'text-success-600' : 'text-secondary-500'}`}>
                        {breaker.enabled ? 'Enabled' : 'Disabled'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-secondary-500">Symbols</p>
                      <p className="font-medium">
                        {breaker.symbols && breaker.symbols.length > 0 
                          ? breaker.symbols.join(', ') 
                          : 'All symbols'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-secondary-500">Exchanges</p>
                      <p className="font-medium">
                        {breaker.exchanges && breaker.exchanges.length > 0 
                          ? breaker.exchanges.join(', ') 
                          : 'All exchanges'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {/* Add new circuit breaker form */}
        {showAddForm ? (
          <div className="card border border-primary-200">
            <h3 className="text-lg font-semibold mb-4">Add New Circuit Breaker</h3>
            <form onSubmit={handleAddCircuitBreaker} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-secondary-700">Name</label>
                  <input
                    type="text"
                    name="name"
                    value={newCondition.name}
                    onChange={handleInputChange}
                    className="input mt-1"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700">Description</label>
                  <input
                    type="text"
                    name="description"
                    value={newCondition.description}
                    onChange={handleInputChange}
                    className="input mt-1"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700">Condition Type</label>
                  <select
                    name="condition_type"
                    value={newCondition.condition_type}
                    onChange={handleInputChange}
                    className="input mt-1"
                    required
                  >
                    {CONDITION_TYPES.map(type => (
                      <option key={type.id} value={type.id}>
                        {type.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700">Threshold</label>
                  <input
                    type="number"
                    name="threshold"
                    value={newCondition.threshold}
                    onChange={handleInputChange}
                    className="input mt-1"
                    required
                    step="0.1"
                  />
                  <p className="text-xs text-secondary-500 mt-1">
                    {newCondition.condition_type === 'max_drawdown' && 'Percent drawdown (e.g., 10 for 10%)'}
                    {newCondition.condition_type === 'max_position_size' && 'Position size in base currency units'}
                    {newCondition.condition_type === 'pnl' && 'Percent P&L threshold'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700">Action</label>
                  <select
                    name="action"
                    value={newCondition.action}
                    onChange={handleInputChange}
                    className="input mt-1"
                    required
                  >
                    {ACTION_TYPES.map(action => (
                      <option key={action.id} value={action.id}>
                        {action.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700">Symbols (comma-separated, leave empty for all)</label>
                  <input
                    type="text"
                    name="symbols"
                    value={newCondition.symbols}
                    onChange={handleInputChange}
                    className="input mt-1"
                    placeholder="E.g., BTCUSDT, ETHUSDT"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700">Exchanges (comma-separated, leave empty for all)</label>
                  <input
                    type="text"
                    name="exchanges"
                    value={newCondition.exchanges}
                    onChange={handleInputChange}
                    className="input mt-1"
                    placeholder="E.g., binance, hyperliquid"
                  />
                </div>
                <div className="flex items-center pt-6">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="enabled"
                      checked={newCondition.enabled}
                      onChange={handleInputChange}
                      className="h-4 w-4 text-primary-600 border-secondary-300 rounded"
                    />
                    <span className="ml-2">Enable condition immediately</span>
                  </label>
                </div>
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                >
                  Add Circuit Breaker
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="flex justify-center">
            <button
              onClick={() => setShowAddForm(true)}
              className="btn btn-primary flex items-center"
            >
              <PlusIcon className="h-5 w-5 mr-1" />
              Add Circuit Breaker
            </button>
          </div>
        )}
      </div>
    );
  };

  // Render the risk limits tab
  const renderRiskLimits = () => {
    return (
      <div className="space-y-6">
        {/* Global Risk Limits */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Global Risk Limits</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-secondary-100 text-secondary-600 text-left">
                  <th className="px-4 py-2">Parameter</th>
                  <th className="px-4 py-2">Value</th>
                  <th className="px-4 py-2">Description</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="px-4 py-2 font-medium">Max Total Exposure</td>
                  <td className="px-4 py-2">${mockRiskLimits.global.max_total_exposure_usd.toLocaleString()}</td>
                  <td className="px-4 py-2 text-secondary-500">Maximum total position value across all exchanges</td>
                </tr>
                <tr className="border-b">
                  <td className="px-4 py-2 font-medium">Max Single Position</td>
                  <td className="px-4 py-2">${mockRiskLimits.global.max_single_position_usd.toLocaleString()}</td>
                  <td className="px-4 py-2 text-secondary-500">Maximum value for any single position</td>
                </tr>
                <tr className="border-b">
                  <td className="px-4 py-2 font-medium">Max Leverage</td>
                  <td className="px-4 py-2">{mockRiskLimits.global.max_leverage}x</td>
                  <td className="px-4 py-2 text-secondary-500">Maximum allowed leverage for any position</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-medium">Max Drawdown</td>
                  <td className="px-4 py-2">{mockRiskLimits.global.max_drawdown_percentage}%</td>
                  <td className="px-4 py-2 text-secondary-500">Maximum allowed drawdown before action is taken</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Symbol-specific Risk Limits */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Symbol-specific Risk Limits</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-secondary-100 text-secondary-600 text-left">
                  <th className="px-4 py-2">Symbol</th>
                  <th className="px-4 py-2">Max Position Size</th>
                  <th className="px-4 py-2">Max Leverage</th>
                  <th className="px-4 py-2">Max Drawdown</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(mockRiskLimits.symbols).map(([symbol, limits]) => (
                  <tr key={symbol} className="border-b">
                    <td className="px-4 py-2 font-medium">{symbol}</td>
                    <td className="px-4 py-2">{limits.max_position_size} {symbol.includes('BTC') ? 'BTC' : 'ETH'}</td>
                    <td className="px-4 py-2">{limits.max_leverage}x</td>
                    <td className="px-4 py-2">{limits.max_drawdown_percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Exchange-specific Risk Limits */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Exchange-specific Risk Limits</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-secondary-100 text-secondary-600 text-left">
                  <th className="px-4 py-2">Exchange</th>
                  <th className="px-4 py-2">Max Total Exposure</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(mockRiskLimits.exchanges).map(([exchange, limits]) => (
                  <tr key={exchange} className="border-b">
                    <td className="px-4 py-2 font-medium capitalize">{exchange}</td>
                    <td className="px-4 py-2">${limits.max_total_exposure_usd.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Render the risk metrics tab
  const renderRiskMetrics = () => {
    return (
      <div className="space-y-6">
        {/* Risk Overview */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Risk Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded shadow">
              <div className="text-sm text-secondary-500 mb-1">Total Equity</div>
              <div className="text-2xl font-bold">${riskMetrics.total_equity?.toLocaleString() || "0"}</div>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <div className="text-sm text-secondary-500 mb-1">Position Value</div>
              <div className="text-2xl font-bold">${riskMetrics.total_position_value?.toLocaleString() || "0"}</div>
              <div className="text-sm text-secondary-500 mt-1">
                <span className={riskMetrics.exposure_percentage > 50 ? "text-danger-500" : "text-primary-500"}>
                  {riskMetrics.exposure_percentage?.toFixed(1) || "0"}% of equity
                </span>
              </div>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <div className="text-sm text-secondary-500 mb-1">Unrealized P&L</div>
              <div className={`text-2xl font-bold ${riskMetrics.total_unrealized_pnl >= 0 ? "text-success-500" : "text-danger-500"}`}>
                ${riskMetrics.total_unrealized_pnl?.toLocaleString() || "0"}
              </div>
              <div className="text-sm text-secondary-500 mt-1">
                {riskMetrics.total_unrealized_pnl_percentage?.toFixed(2) || "0"}%
              </div>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <div className="text-sm text-secondary-500 mb-1">Active Positions</div>
              <div className="text-2xl font-bold">{riskMetrics.position_count || "0"}</div>
            </div>
          </div>
        </div>
        
        {/* Drawdown Metrics */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Drawdown Metrics</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-secondary-100 text-secondary-600 text-left">
                  <th className="px-4 py-2">Period</th>
                  <th className="px-4 py-2">Drawdown</th>
                  <th className="px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="px-4 py-2 font-medium">Daily</td>
                  <td className="px-4 py-2">{riskMetrics.drawdown?.daily?.toFixed(2) || "0"}%</td>
                  <td className="px-4 py-2">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getDrawdownStatusClass(riskMetrics.drawdown?.daily, 5, 10)}`}>
                      {getDrawdownStatus(riskMetrics.drawdown?.daily, 5, 10)}
                    </span>
                  </td>
                </tr>
                <tr className="border-b">
                  <td className="px-4 py-2 font-medium">Weekly</td>
                  <td className="px-4 py-2">{riskMetrics.drawdown?.weekly?.toFixed(2) || "0"}%</td>
                  <td className="px-4 py-2">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getDrawdownStatusClass(riskMetrics.drawdown?.weekly, 10, 15)}`}>
                      {getDrawdownStatus(riskMetrics.drawdown?.weekly, 10, 15)}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-medium">Monthly</td>
                  <td className="px-4 py-2">{riskMetrics.drawdown?.monthly?.toFixed(2) || "0"}%</td>
                  <td className="px-4 py-2">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getDrawdownStatusClass(riskMetrics.drawdown?.monthly, 15, 25)}`}>
                      {getDrawdownStatus(riskMetrics.drawdown?.monthly, 15, 25)}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Position Metrics */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Position Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded shadow">
              <h4 className="text-md font-medium mb-2">Largest Position</h4>
              <div className="text-sm mb-1">
                <span className="text-secondary-500">Symbol:</span> {riskMetrics.largest_position?.symbol || "N/A"}
              </div>
              <div className="text-sm mb-1">
                <span className="text-secondary-500">Exchange:</span> {riskMetrics.largest_position?.exchange || "N/A"}
              </div>
              <div className="text-sm mb-1">
                <span className="text-secondary-500">Value:</span> ${riskMetrics.largest_position?.value?.toLocaleString() || "0"}
              </div>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h4 className="text-md font-medium mb-2">Highest Leverage</h4>
              <div className="text-sm mb-1">
                <span className="text-secondary-500">Symbol:</span> {riskMetrics.highest_leverage?.symbol || "N/A"}
              </div>
              <div className="text-sm mb-1">
                <span className="text-secondary-500">Exchange:</span> {riskMetrics.highest_leverage?.exchange || "N/A"}
              </div>
              <div className="text-sm mb-1">
                <span className="text-secondary-500">Leverage:</span> {riskMetrics.highest_leverage?.leverage?.toFixed(1) || "0"}x
              </div>
            </div>
          </div>
        </div>
        
        {/* Exchange-specific Metrics */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Exchange-specific Metrics</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-secondary-100 text-secondary-600 text-left">
                  <th className="px-4 py-2">Exchange</th>
                  <th className="px-4 py-2">Positions</th>
                  <th className="px-4 py-2">Position Value</th>
                  <th className="px-4 py-2">Unrealized P&L</th>
                  <th className="px-4 py-2">Exposure %</th>
                </tr>
              </thead>
              <tbody>
                {riskMetrics.positions_by_exchange && Object.entries(riskMetrics.positions_by_exchange).map(([exchange, data]) => (
                  <tr key={exchange} className="border-b">
                    <td className="px-4 py-2 font-medium capitalize">{exchange}</td>
                    <td className="px-4 py-2">{data.position_count || 0}</td>
                    <td className="px-4 py-2">${data.position_value?.toLocaleString() || "0"}</td>
                    <td className="px-4 py-2">
                      <span className={data.unrealized_pnl >= 0 ? "text-success-500" : "text-danger-500"}>
                        ${data.unrealized_pnl?.toLocaleString() || "0"}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <span className={data.exposure_percentage > 50 ? "text-danger-500" : "text-primary-500"}>
                        {data.exposure_percentage?.toFixed(1) || "0"}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Last updated timestamp */}
        {lastUpdated && (
          <div className="text-sm text-secondary-500 text-right">
            Last updated: {lastUpdated.toLocaleTimeString()}
            {isRiskMetricsConnected && (
              <span className="ml-2 animate-pulse text-success-500">• Live</span>
            )}
          </div>
        )}
      </div>
    );
  };

  // Helper function to determine drawdown status
  const getDrawdownStatus = (drawdown, warningThreshold, dangerThreshold) => {
    if (!drawdown) return 'Normal';
    if (drawdown >= dangerThreshold) return 'High Risk';
    if (drawdown >= warningThreshold) return 'Warning';
    return 'Normal';
  };

  // Helper function to get the appropriate CSS class for drawdown status
  const getDrawdownStatusClass = (drawdown, warningThreshold, dangerThreshold) => {
    if (!drawdown) return 'bg-success-100 text-success-800';
    if (drawdown >= dangerThreshold) return 'bg-danger-100 text-danger-800';
    if (drawdown >= warningThreshold) return 'bg-warning-100 text-warning-800';
    return 'bg-success-100 text-success-800';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Risk Management</h1>
        <div className="flex items-center space-x-4">
          {/* WebSocket Status Indicators */}
          <WebSocketStatus 
            status={riskMetricsStatus} 
            channel="Risk Metrics" 
            error={riskMetricsError}
            onReconnect={connectRiskMetricsWs}
          />
          <WebSocketStatus 
            status={alertsStatus} 
            channel="Alerts" 
            error={alertsError}
            onReconnect={connectAlertsWs}
          />
        </div>
      </div>

      {error && (
        <div className="bg-danger-100 border border-danger-400 text-danger-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      {/* Tab navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex">
          <button
            className={`py-2 px-4 text-center border-b-2 font-medium text-sm ${
              activeTab === 'circuit_breakers'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('circuit_breakers')}
          >
            Circuit Breakers
          </button>
          <button
            className={`py-2 px-4 text-center border-b-2 font-medium text-sm ${
              activeTab === 'risk_limits'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('risk_limits')}
          >
            Risk Limits
          </button>
          <button
            className={`py-2 px-4 text-center border-b-2 font-medium text-sm ${
              activeTab === 'risk_metrics'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('risk_metrics')}
          >
            Risk Metrics
          </button>
        </nav>
      </div>

      {/* Tab content */}
      <div className="mt-6">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="loader">Loading...</div>
          </div>
        ) : (
          <>
            {activeTab === 'circuit_breakers' && renderCircuitBreakers()}
            {activeTab === 'risk_limits' && renderRiskLimits()}
            {activeTab === 'risk_metrics' && renderRiskMetrics()}
          </>
        )}
      </div>
    </div>
  );
} 