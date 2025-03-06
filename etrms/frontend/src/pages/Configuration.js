import { useState, useEffect } from 'react';
import axios from 'axios';
import { Cog6ToothIcon, ArrowPathIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

export default function Configuration() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('system'); // 'system', 'exchanges', 'logging', 'risk'
  const [config, setConfig] = useState({
    system: {
      api_title: "Enhanced Trading Risk Management System API",
      api_description: "API for managing trading risk, analyzing markets, and providing AI-powered trading assistance",
      api_version: "0.1.0",
      api_prefix: "/api",
      cors_origins: ["*"],
      cors_allow_credentials: true,
      cors_allow_methods: ["*"],
      cors_allow_headers: ["*"]
    },
    exchanges: {
      binance: {
        api_key: "••••••••••••••••",
        api_secret: "••••••••••••••••",
        testnet: true
      },
      hyperliquid: {
        api_key: "••••••••••••••••",
        api_secret: "••••••••••••••••"
      }
    },
    ai_assistant: {
      api_key: "••••••••••••••••",
      model: "claude-3-opus-20240229"
    },
    logging: {
      log_level: "INFO",
      log_to_file: true,
      log_file_path: "/var/log/etrms/app.log",
      log_rotation: "daily",
      log_retention: 30
    },
    database: {
      host: "localhost",
      port: 5432,
      name: "etrms",
      user: "postgres"
    },
    risk: {
      global: {
        position_max_drawdown_percentage: 5.0,
        position_trailing_stop_multiplier: 1.5,
        daily_max_drawdown_percentage: 10.0,
        weekly_max_drawdown_percentage: 15.0,
        monthly_max_drawdown_percentage: 20.0,
        max_position_size_percentage: 5.0,
        max_correlated_exposure_percentage: 15.0,
        risk_per_trade_percentage: 1.0,
        volatility_adjustment_factor: 1.0,
        cooling_off_period_minutes: 60,
        consecutive_loss_threshold: 3
      },
      symbols: {
        "BTCUSDT": {
          max_position_size_percentage: 7.5,
          max_leverage: 5,
          position_max_drawdown_percentage: 7.0,
          risk_per_trade_percentage: 1.5
        },
        "ETHUSDT": {
          max_position_size_percentage: 6.0,
          max_leverage: 4,
          position_max_drawdown_percentage: 6.0,
          risk_per_trade_percentage: 1.2
        }
      },
      exchanges: {
        "binance": {
          max_leverage: 5,
          max_positions: 10
        },
        "hyperliquid": {
          max_leverage: 3,
          max_positions: 5
        }
      },
      circuit_breakers: [
        {
          name: "daily_drawdown",
          description: "Close all positions if daily drawdown exceeds threshold",
          enabled: true,
          condition: "daily_drawdown_percentage > daily_max_drawdown_percentage",
          action: "close_all_positions",
          parameters: {
            notification: true,
            cooling_off: true
          }
        },
        {
          name: "consecutive_losses",
          description: "Reduce position size after consecutive losses",
          enabled: true,
          condition: "consecutive_losses >= consecutive_loss_threshold",
          action: "reduce_position_size",
          parameters: {
            reduction_factor: 0.5,
            notification: true
          }
        }
      ]
    }
  });
  const [editedConfig, setEditedConfig] = useState({});
  const [isEditing, setIsEditing] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Fetch configuration data
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        setLoading(true);
        // In a real app, this would be an API call
        // const response = await axios.get('/api/config');
        // setConfig(response.data);
        
        // Using mock data for now
        setTimeout(() => {
          setLoading(false);
        }, 500);
      } catch (err) {
        console.error('Error fetching configuration:', err);
        setError('Failed to fetch configuration. Please try again.');
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  // Handle input changes
  const handleInputChange = (section, key, value) => {
    setEditedConfig(prev => ({
      ...prev,
      [section]: {
        ...(prev[section] || {}),
        [key]: value
      }
    }));
  };

  // Handle saving configuration
  const handleSaveConfig = async () => {
    try {
      setLoading(true);
      // In a real app, this would be an API call
      // await axios.put('/api/config', editedConfig);
      
      // Update local state
      setConfig(prev => {
        const newConfig = { ...prev };
        Object.entries(editedConfig).forEach(([section, values]) => {
          newConfig[section] = { ...newConfig[section], ...values };
        });
        return newConfig;
      });
      
      setEditedConfig({});
      setIsEditing(false);
      setSaveSuccess(true);
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSaveSuccess(false);
      }, 3000);
      
      setLoading(false);
    } catch (err) {
      console.error('Error saving configuration:', err);
      setError('Failed to save configuration. Please try again.');
      setLoading(false);
    }
  };

  // Handle resetting configuration
  const handleResetConfig = async () => {
    if (!window.confirm("Are you sure you want to reset the configuration to default values? This cannot be undone.")) {
      return;
    }
    
    try {
      setLoading(true);
      // In a real app, this would be an API call
      // await axios.post('/api/config/reset');
      // const response = await axios.get('/api/config');
      // setConfig(response.data);
      
      // Using mock response for now
      setTimeout(() => {
        // Reset to initial state
        setEditedConfig({});
        setIsEditing(false);
        setSaveSuccess(true);
        
        // Clear success message after 3 seconds
        setTimeout(() => {
          setSaveSuccess(false);
        }, 3000);
        
        setLoading(false);
      }, 500);
    } catch (err) {
      console.error('Error resetting configuration:', err);
      setError('Failed to reset configuration. Please try again.');
      setLoading(false);
    }
  };

  // Render the system configuration tab
  const renderSystemConfig = () => {
    const systemConfig = config.system;
    
    return (
      <div className="space-y-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">API Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700">API Title</label>
              <input
                type="text"
                value={editedConfig.system?.api_title ?? systemConfig.api_title}
                onChange={(e) => handleInputChange('system', 'api_title', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">API Version</label>
              <input
                type="text"
                value={editedConfig.system?.api_version ?? systemConfig.api_version}
                onChange={(e) => handleInputChange('system', 'api_version', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-secondary-700">API Description</label>
              <textarea
                value={editedConfig.system?.api_description ?? systemConfig.api_description}
                onChange={(e) => handleInputChange('system', 'api_description', e.target.value)}
                className="input mt-1"
                rows="2"
                disabled={!isEditing}
              ></textarea>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">API Prefix</label>
              <input
                type="text"
                value={editedConfig.system?.api_prefix ?? systemConfig.api_prefix}
                onChange={(e) => handleInputChange('system', 'api_prefix', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">CORS Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-secondary-700">CORS Origins (comma-separated)</label>
              <input
                type="text"
                value={(editedConfig.system?.cors_origins ?? systemConfig.cors_origins).join(', ')}
                onChange={(e) => handleInputChange('system', 'cors_origins', e.target.value.split(',').map(s => s.trim()))}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={editedConfig.system?.cors_allow_credentials ?? systemConfig.cors_allow_credentials}
                  onChange={(e) => handleInputChange('system', 'cors_allow_credentials', e.target.checked)}
                  className="h-4 w-4 text-primary-600 border-secondary-300 rounded"
                  disabled={!isEditing}
                />
                <span className="ml-2">Allow Credentials</span>
              </label>
            </div>
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Database Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700">Host</label>
              <input
                type="text"
                value={editedConfig.database?.host ?? config.database.host}
                onChange={(e) => handleInputChange('database', 'host', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Port</label>
              <input
                type="number"
                value={editedConfig.database?.port ?? config.database.port}
                onChange={(e) => handleInputChange('database', 'port', parseInt(e.target.value))}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Database Name</label>
              <input
                type="text"
                value={editedConfig.database?.name ?? config.database.name}
                onChange={(e) => handleInputChange('database', 'name', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">User</label>
              <input
                type="text"
                value={editedConfig.database?.user ?? config.database.user}
                onChange={(e) => handleInputChange('database', 'user', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Password</label>
              <input
                type="password"
                value={editedConfig.database?.password ?? "••••••••"}
                onChange={(e) => handleInputChange('database', 'password', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
                placeholder="••••••••"
              />
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render the exchanges configuration tab
  const renderExchangesConfig = () => {
    const exchangesConfig = config.exchanges;
    
    return (
      <div className="space-y-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Binance Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700">API Key</label>
              <input
                type="password"
                value={editedConfig.exchanges?.binance?.api_key ?? exchangesConfig.binance.api_key}
                onChange={(e) => handleInputChange('exchanges', 'binance', {
                  ...exchangesConfig.binance,
                  ...editedConfig.exchanges?.binance,
                  api_key: e.target.value
                })}
                className="input mt-1"
                disabled={!isEditing}
                placeholder="••••••••••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">API Secret</label>
              <input
                type="password"
                value={editedConfig.exchanges?.binance?.api_secret ?? exchangesConfig.binance.api_secret}
                onChange={(e) => handleInputChange('exchanges', 'binance', {
                  ...exchangesConfig.binance,
                  ...editedConfig.exchanges?.binance,
                  api_secret: e.target.value
                })}
                className="input mt-1"
                disabled={!isEditing}
                placeholder="••••••••••••••••"
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={
                    editedConfig.exchanges?.binance?.testnet !== undefined
                      ? editedConfig.exchanges.binance.testnet
                      : exchangesConfig.binance.testnet
                  }
                  onChange={(e) => handleInputChange('exchanges', 'binance', {
                    ...exchangesConfig.binance,
                    ...editedConfig.exchanges?.binance,
                    testnet: e.target.checked
                  })}
                  className="h-4 w-4 text-primary-600 border-secondary-300 rounded"
                  disabled={!isEditing}
                />
                <span className="ml-2">Use Testnet</span>
              </label>
            </div>
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Hyperliquid Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700">API Key</label>
              <input
                type="password"
                value={editedConfig.exchanges?.hyperliquid?.api_key ?? exchangesConfig.hyperliquid.api_key}
                onChange={(e) => handleInputChange('exchanges', 'hyperliquid', {
                  ...exchangesConfig.hyperliquid,
                  ...editedConfig.exchanges?.hyperliquid,
                  api_key: e.target.value
                })}
                className="input mt-1"
                disabled={!isEditing}
                placeholder="••••••••••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">API Secret</label>
              <input
                type="password"
                value={editedConfig.exchanges?.hyperliquid?.api_secret ?? exchangesConfig.hyperliquid.api_secret}
                onChange={(e) => handleInputChange('exchanges', 'hyperliquid', {
                  ...exchangesConfig.hyperliquid,
                  ...editedConfig.exchanges?.hyperliquid,
                  api_secret: e.target.value
                })}
                className="input mt-1"
                disabled={!isEditing}
                placeholder="••••••••••••••••"
              />
            </div>
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">AI Assistant Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700">API Key</label>
              <input
                type="password"
                value={editedConfig.ai_assistant?.api_key ?? config.ai_assistant.api_key}
                onChange={(e) => handleInputChange('ai_assistant', 'api_key', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
                placeholder="••••••••••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Model</label>
              <select
                value={editedConfig.ai_assistant?.model ?? config.ai_assistant.model}
                onChange={(e) => handleInputChange('ai_assistant', 'model', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
              >
                <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render the logging configuration tab
  const renderLoggingConfig = () => {
    const loggingConfig = config.logging;
    
    return (
      <div className="space-y-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Logging Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700">Log Level</label>
              <select
                value={editedConfig.logging?.log_level ?? loggingConfig.log_level}
                onChange={(e) => handleInputChange('logging', 'log_level', e.target.value)}
                className="input mt-1"
                disabled={!isEditing}
              >
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={editedConfig.logging?.log_to_file ?? loggingConfig.log_to_file}
                  onChange={(e) => handleInputChange('logging', 'log_to_file', e.target.checked)}
                  className="h-4 w-4 text-primary-600 border-secondary-300 rounded"
                  disabled={!isEditing}
                />
                <span className="ml-2">Log to File</span>
              </label>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-secondary-700">Log File Path</label>
              <input
                type="text"
                value={editedConfig.logging?.log_file_path ?? loggingConfig.log_file_path}
                onChange={(e) => handleInputChange('logging', 'log_file_path', e.target.value)}
                className="input mt-1"
                disabled={!isEditing || !(editedConfig.logging?.log_to_file ?? loggingConfig.log_to_file)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Log Rotation</label>
              <select
                value={editedConfig.logging?.log_rotation ?? loggingConfig.log_rotation}
                onChange={(e) => handleInputChange('logging', 'log_rotation', e.target.value)}
                className="input mt-1"
                disabled={!isEditing || !(editedConfig.logging?.log_to_file ?? loggingConfig.log_to_file)}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="size">Size-based (10MB)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Log Retention (days)</label>
              <input
                type="number"
                value={editedConfig.logging?.log_retention ?? loggingConfig.log_retention}
                onChange={(e) => handleInputChange('logging', 'log_retention', parseInt(e.target.value))}
                className="input mt-1"
                disabled={!isEditing || !(editedConfig.logging?.log_to_file ?? loggingConfig.log_to_file)}
              />
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render the risk management configuration tab
  const renderRiskConfig = () => {
    const riskConfig = config.risk;
    
    return (
      <div className="space-y-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Global Risk Parameters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700">Max Position Drawdown (%)</label>
              <input
                type="number"
                value={editedConfig.risk?.global?.position_max_drawdown_percentage ?? riskConfig.global.position_max_drawdown_percentage}
                onChange={(e) => handleInputChange('risk', 'global', {
                  ...riskConfig.global,
                  ...editedConfig.risk?.global,
                  position_max_drawdown_percentage: parseFloat(e.target.value)
                })}
                className="input mt-1"
                disabled={!isEditing}
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Trailing Stop Multiplier</label>
              <input
                type="number"
                value={editedConfig.risk?.global?.position_trailing_stop_multiplier ?? riskConfig.global.position_trailing_stop_multiplier}
                onChange={(e) => handleInputChange('risk', 'global', {
                  ...riskConfig.global,
                  ...editedConfig.risk?.global,
                  position_trailing_stop_multiplier: parseFloat(e.target.value)
                })}
                className="input mt-1"
                disabled={!isEditing}
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Daily Max Drawdown (%)</label>
              <input
                type="number"
                value={editedConfig.risk?.global?.daily_max_drawdown_percentage ?? riskConfig.global.daily_max_drawdown_percentage}
                onChange={(e) => handleInputChange('risk', 'global', {
                  ...riskConfig.global,
                  ...editedConfig.risk?.global,
                  daily_max_drawdown_percentage: parseFloat(e.target.value)
                })}
                className="input mt-1"
                disabled={!isEditing}
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Weekly Max Drawdown (%)</label>
              <input
                type="number"
                value={editedConfig.risk?.global?.weekly_max_drawdown_percentage ?? riskConfig.global.weekly_max_drawdown_percentage}
                onChange={(e) => handleInputChange('risk', 'global', {
                  ...riskConfig.global,
                  ...editedConfig.risk?.global,
                  weekly_max_drawdown_percentage: parseFloat(e.target.value)
                })}
                className="input mt-1"
                disabled={!isEditing}
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Monthly Max Drawdown (%)</label>
              <input
                type="number"
                value={editedConfig.risk?.global?.monthly_max_drawdown_percentage ?? riskConfig.global.monthly_max_drawdown_percentage}
                onChange={(e) => handleInputChange('risk', 'global', {
                  ...riskConfig.global,
                  ...editedConfig.risk?.global,
                  monthly_max_drawdown_percentage: parseFloat(e.target.value)
                })}
                className="input mt-1"
                disabled={!isEditing}
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Max Position Size (%)</label>
              <input
                type="number"
                value={editedConfig.risk?.global?.max_position_size_percentage ?? riskConfig.global.max_position_size_percentage}
                onChange={(e) => handleInputChange('risk', 'global', {
                  ...riskConfig.global,
                  ...editedConfig.risk?.global,
                  max_position_size_percentage: parseFloat(e.target.value)
                })}
                className="input mt-1"
                disabled={!isEditing}
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Risk Per Trade (%)</label>
              <input
                type="number"
                value={editedConfig.risk?.global?.risk_per_trade_percentage ?? riskConfig.global.risk_per_trade_percentage}
                onChange={(e) => handleInputChange('risk', 'global', {
                  ...riskConfig.global,
                  ...editedConfig.risk?.global,
                  risk_per_trade_percentage: parseFloat(e.target.value)
                })}
                className="input mt-1"
                disabled={!isEditing}
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Cooling Off Period (minutes)</label>
              <input
                type="number"
                value={editedConfig.risk?.global?.cooling_off_period_minutes ?? riskConfig.global.cooling_off_period_minutes}
                onChange={(e) => handleInputChange('risk', 'global', {
                  ...riskConfig.global,
                  ...editedConfig.risk?.global,
                  cooling_off_period_minutes: parseInt(e.target.value)
                })}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700">Consecutive Loss Threshold</label>
              <input
                type="number"
                value={editedConfig.risk?.global?.consecutive_loss_threshold ?? riskConfig.global.consecutive_loss_threshold}
                onChange={(e) => handleInputChange('risk', 'global', {
                  ...riskConfig.global,
                  ...editedConfig.risk?.global,
                  consecutive_loss_threshold: parseInt(e.target.value)
                })}
                className="input mt-1"
                disabled={!isEditing}
              />
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Symbol-Specific Risk Parameters</h3>
            {isEditing && (
              <button
                onClick={() => {
                  const symbol = prompt("Enter symbol (e.g., BTCUSDT):");
                  if (symbol) {
                    const newSymbolConfig = {
                      max_position_size_percentage: 5.0,
                      max_leverage: 3,
                      position_max_drawdown_percentage: 5.0,
                      risk_per_trade_percentage: 1.0
                    };
                    
                    handleInputChange('risk', 'symbols', {
                      ...riskConfig.symbols,
                      ...editedConfig.risk?.symbols,
                      [symbol]: newSymbolConfig
                    });
                  }
                }}
                className="btn btn-sm btn-secondary"
              >
                Add Symbol
              </button>
            )}
          </div>
          <div className="space-y-4">
            {Object.entries(editedConfig.risk?.symbols ?? riskConfig.symbols).map(([symbol, settings]) => (
              <div key={symbol} className="border border-secondary-200 rounded-md p-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-semibold">{symbol}</h4>
                  {isEditing && (
                    <button
                      onClick={() => {
                        if (window.confirm(`Remove ${symbol} configuration?`)) {
                          const updatedSymbols = { ...editedConfig.risk?.symbols ?? riskConfig.symbols };
                          delete updatedSymbols[symbol];
                          handleInputChange('risk', 'symbols', updatedSymbols);
                        }
                      }}
                      className="text-danger-500 hover:text-danger-700 text-sm"
                    >
                      Remove
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-secondary-700">Max Position Size (%)</label>
                    <input
                      type="number"
                      value={
                        (editedConfig.risk?.symbols?.[symbol]?.max_position_size_percentage !== undefined) 
                          ? editedConfig.risk.symbols[symbol].max_position_size_percentage 
                          : settings.max_position_size_percentage
                      }
                      onChange={(e) => {
                        const updatedSymbolConfig = {
                          ...(editedConfig.risk?.symbols?.[symbol] ?? settings),
                          max_position_size_percentage: parseFloat(e.target.value)
                        };
                        
                        handleInputChange('risk', 'symbols', {
                          ...editedConfig.risk?.symbols ?? riskConfig.symbols,
                          [symbol]: updatedSymbolConfig
                        });
                      }}
                      className="input mt-1"
                      disabled={!isEditing}
                      step="0.1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-secondary-700">Max Leverage</label>
                    <input
                      type="number"
                      value={
                        (editedConfig.risk?.symbols?.[symbol]?.max_leverage !== undefined) 
                          ? editedConfig.risk.symbols[symbol].max_leverage 
                          : settings.max_leverage
                      }
                      onChange={(e) => {
                        const updatedSymbolConfig = {
                          ...(editedConfig.risk?.symbols?.[symbol] ?? settings),
                          max_leverage: parseInt(e.target.value)
                        };
                        
                        handleInputChange('risk', 'symbols', {
                          ...editedConfig.risk?.symbols ?? riskConfig.symbols,
                          [symbol]: updatedSymbolConfig
                        });
                      }}
                      className="input mt-1"
                      disabled={!isEditing}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Exchange-Specific Risk Parameters</h3>
          <div className="space-y-4">
            {Object.entries(editedConfig.risk?.exchanges ?? riskConfig.exchanges).map(([exchange, settings]) => (
              <div key={exchange} className="border border-secondary-200 rounded-md p-4">
                <div className="mb-2">
                  <h4 className="font-semibold">{exchange.charAt(0).toUpperCase() + exchange.slice(1)}</h4>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-secondary-700">Max Leverage</label>
                    <input
                      type="number"
                      value={
                        (editedConfig.risk?.exchanges?.[exchange]?.max_leverage !== undefined) 
                          ? editedConfig.risk.exchanges[exchange].max_leverage 
                          : settings.max_leverage
                      }
                      onChange={(e) => {
                        const updatedExchangeConfig = {
                          ...(editedConfig.risk?.exchanges?.[exchange] ?? settings),
                          max_leverage: parseInt(e.target.value)
                        };
                        
                        handleInputChange('risk', 'exchanges', {
                          ...editedConfig.risk?.exchanges ?? riskConfig.exchanges,
                          [exchange]: updatedExchangeConfig
                        });
                      }}
                      className="input mt-1"
                      disabled={!isEditing}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-secondary-700">Max Positions</label>
                    <input
                      type="number"
                      value={
                        (editedConfig.risk?.exchanges?.[exchange]?.max_positions !== undefined) 
                          ? editedConfig.risk.exchanges[exchange].max_positions 
                          : settings.max_positions
                      }
                      onChange={(e) => {
                        const updatedExchangeConfig = {
                          ...(editedConfig.risk?.exchanges?.[exchange] ?? settings),
                          max_positions: parseInt(e.target.value)
                        };
                        
                        handleInputChange('risk', 'exchanges', {
                          ...editedConfig.risk?.exchanges ?? riskConfig.exchanges,
                          [exchange]: updatedExchangeConfig
                        });
                      }}
                      className="input mt-1"
                      disabled={!isEditing}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Circuit Breakers</h3>
            {isEditing && (
              <button
                onClick={() => {
                  const name = prompt("Enter circuit breaker name:");
                  if (name) {
                    const newCircuitBreaker = {
                      name,
                      description: "New circuit breaker",
                      enabled: true,
                      condition: "",
                      action: "notify",
                      parameters: { notification: true }
                    };
                    
                    const updatedCircuitBreakers = [
                      ...(editedConfig.risk?.circuit_breakers ?? riskConfig.circuit_breakers),
                      newCircuitBreaker
                    ];
                    
                    handleInputChange('risk', 'circuit_breakers', updatedCircuitBreakers);
                  }
                }}
                className="btn btn-sm btn-secondary"
              >
                Add Circuit Breaker
              </button>
            )}
          </div>
          <div className="space-y-4">
            {(editedConfig.risk?.circuit_breakers ?? riskConfig.circuit_breakers).map((breaker, index) => (
              <div key={breaker.name} className="border border-secondary-200 rounded-md p-4">
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center space-x-3">
                    <h4 className="font-semibold">{breaker.name}</h4>
                    <span className={`text-xs px-2 py-1 rounded-full ${breaker.enabled ? 'bg-success-100 text-success-800' : 'bg-secondary-100 text-secondary-800'}`}>
                      {breaker.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  {isEditing && (
                    <button
                      onClick={() => {
                        if (window.confirm(`Remove ${breaker.name} circuit breaker?`)) {
                          const updatedBreakers = (
                            editedConfig.risk?.circuit_breakers ?? [...riskConfig.circuit_breakers]
                          ).filter((b, i) => i !== index);
                          
                          handleInputChange('risk', 'circuit_breakers', updatedBreakers);
                        }
                      }}
                      className="text-danger-500 hover:text-danger-700 text-sm"
                    >
                      Remove
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-secondary-700">Description</label>
                    <input
                      type="text"
                      value={breaker.description}
                      onChange={(e) => {
                        const updatedBreakers = (
                          editedConfig.risk?.circuit_breakers ?? [...riskConfig.circuit_breakers]
                        ).map((b, i) => i === index ? { ...b, description: e.target.value } : b);
                        
                        handleInputChange('risk', 'circuit_breakers', updatedBreakers);
                      }}
                      className="input mt-1 w-full"
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={breaker.enabled}
                      onChange={(e) => {
                        const updatedBreakers = (
                          editedConfig.risk?.circuit_breakers ?? [...riskConfig.circuit_breakers]
                        ).map((b, i) => i === index ? { ...b, enabled: e.target.checked } : b);
                        
                        handleInputChange('risk', 'circuit_breakers', updatedBreakers);
                      }}
                      className="h-4 w-4 text-primary-600 border-secondary-300 rounded"
                      disabled={!isEditing}
                    />
                    <label className="ml-2 text-sm">Enabled</label>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-secondary-700">Condition</label>
                    <input
                      type="text"
                      value={breaker.condition}
                      onChange={(e) => {
                        const updatedBreakers = (
                          editedConfig.risk?.circuit_breakers ?? [...riskConfig.circuit_breakers]
                        ).map((b, i) => i === index ? { ...b, condition: e.target.value } : b);
                        
                        handleInputChange('risk', 'circuit_breakers', updatedBreakers);
                      }}
                      className="input mt-1 w-full"
                      disabled={!isEditing}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-secondary-700">Action</label>
                    <select
                      value={breaker.action}
                      onChange={(e) => {
                        const updatedBreakers = (
                          editedConfig.risk?.circuit_breakers ?? [...riskConfig.circuit_breakers]
                        ).map((b, i) => i === index ? { ...b, action: e.target.value } : b);
                        
                        handleInputChange('risk', 'circuit_breakers', updatedBreakers);
                      }}
                      className="input mt-1 w-full"
                      disabled={!isEditing}
                    >
                      <option value="notify">Notify Only</option>
                      <option value="close_position">Close Position</option>
                      <option value="close_all_positions">Close All Positions</option>
                      <option value="reduce_position_size">Reduce Position Size</option>
                      <option value="reduce_leverage">Reduce Leverage</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Configuration</h1>
        <div className="flex space-x-2">
          {isEditing ? (
            <>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setEditedConfig({});
                }}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveConfig}
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleResetConfig}
                className="btn btn-secondary flex items-center"
                disabled={loading}
              >
                <ArrowPathIcon className="h-5 w-5 mr-1" />
                Reset to Default
              </button>
              <button
                onClick={() => setIsEditing(true)}
                className="btn btn-primary flex items-center"
              >
                <Cog6ToothIcon className="h-5 w-5 mr-1" />
                Edit Configuration
              </button>
            </>
          )}
        </div>
      </div>

      {saveSuccess && (
        <div className="bg-success-100 border border-success-400 text-success-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Success:</strong>
          <span className="block sm:inline"> Configuration saved successfully.</span>
        </div>
      )}

      {error && (
        <div className="bg-danger-100 border border-danger-400 text-danger-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-secondary-200">
        <nav className="-mb-px flex">
          <button
            onClick={() => setActiveTab('system')}
            className={`py-2 px-4 border-b-2 font-medium text-sm ${
              activeTab === 'system'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
            }`}
          >
            System
          </button>
          <button
            onClick={() => setActiveTab('exchanges')}
            className={`py-2 px-4 border-b-2 font-medium text-sm ${
              activeTab === 'exchanges'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
            }`}
          >
            Exchanges & AI
          </button>
          <button
            onClick={() => setActiveTab('risk')}
            className={`py-2 px-4 border-b-2 font-medium text-sm ${
              activeTab === 'risk'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
            }`}
          >
            Risk Management
          </button>
          <button
            onClick={() => setActiveTab('logging')}
            className={`py-2 px-4 border-b-2 font-medium text-sm ${
              activeTab === 'logging'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
            }`}
          >
            Logging
          </button>
        </nav>
      </div>

      {loading && !config ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      ) : (
        <div className="mt-6">
          {activeTab === 'system' && renderSystemConfig()}
          {activeTab === 'exchanges' && renderExchangesConfig()}
          {activeTab === 'risk' && renderRiskConfig()}
          {activeTab === 'logging' && renderLoggingConfig()}
        </div>
      )}
    </div>
  );
} 