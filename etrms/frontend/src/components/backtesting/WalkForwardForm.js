import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ArrowPathIcon, 
  CalendarIcon, 
  ArrowsRightLeftIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  PlusIcon,
  MinusIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

const DEFAULT_FORM_VALUES = {
  strategy_name: '',
  parameter_grid: {},
  symbols: ['BTC-USDT'],
  timeframe: '1h',
  start_date: '',
  end_date: '',
  initial_balance: 10000,
  fee_rate: 0.0004,
  slippage: 0.0001,
  risk_per_trade: 0.01,
  optimization_metric: 'sharpe_ratio',
  window_size_days: 90,
  step_size_days: 30,
  in_sample_pct: 0.7,
  save_results: true
};

const TIMEFRAMES = [
  { value: '1m', label: '1 minute' },
  { value: '5m', label: '5 minutes' },
  { value: '15m', label: '15 minutes' },
  { value: '30m', label: '30 minutes' },
  { value: '1h', label: '1 hour' },
  { value: '4h', label: '4 hours' },
  { value: '1d', label: '1 day' },
  { value: '1w', label: '1 week' }
];

const OPTIMIZATION_METRICS = [
  { value: 'sharpe_ratio', label: 'Sharpe Ratio' },
  { value: 'sortino_ratio', label: 'Sortino Ratio' },
  { value: 'calmar_ratio', label: 'Calmar Ratio' },
  { value: 'total_return', label: 'Total Return' },
  { value: 'profit_factor', label: 'Profit Factor' },
  { value: 'win_rate', label: 'Win Rate' },
  { value: 'expectancy', label: 'Expectancy' },
  { value: 'max_drawdown', label: 'Max Drawdown (minimized)' },
];

function WalkForwardForm({ strategies = [], onTaskCreated }) {
  const [formValues, setFormValues] = useState(DEFAULT_FORM_VALUES);
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [strategyParams, setStrategyParams] = useState({});
  const [paramRanges, setParamRanges] = useState([]);
  const [gridCombinations, setGridCombinations] = useState(0);
  const [windowCount, setWindowCount] = useState(0);

  // Update strategy parameters based on selected strategy
  useEffect(() => {
    if (formValues.strategy_name) {
      fetchStrategyParameters(formValues.strategy_name);
    }
  }, [formValues.strategy_name]);

  // Update window count when dates or window parameters change
  useEffect(() => {
    calculateWindowCount();
  }, [formValues.start_date, formValues.end_date, formValues.window_size_days, formValues.step_size_days]);

  // Calculate total grid combinations whenever paramRanges changes
  useEffect(() => {
    calculateGridCombinations();
  }, [paramRanges]);

  const fetchStrategyParameters = async (strategyName) => {
    const strategy = strategies.find(s => s.name === strategyName);
    if (strategy && strategy.parameters) {
      setStrategyParams(strategy.parameters);
      
      // Initialize parameter ranges based on strategy default values
      const initialRanges = [];
      Object.entries(strategy.parameters).forEach(([paramName, paramConfig]) => {
        initialRanges.push({
          name: paramName,
          type: paramConfig.type,
          values: [paramConfig.default],
          min: paramConfig.min,
          max: paramConfig.max,
          description: paramConfig.description || '',
          enabled: false
        });
      });
      
      setParamRanges(initialRanges);
    } else {
      setStrategyParams({});
      setParamRanges([]);
    }
  };

  const calculateWindowCount = () => {
    if (!formValues.start_date || !formValues.end_date) {
      setWindowCount(0);
      return;
    }

    const startDate = new Date(formValues.start_date);
    const endDate = new Date(formValues.end_date);
    
    // Calculate total days in the date range
    const totalDays = (endDate - startDate) / (1000 * 60 * 60 * 24);
    
    if (totalDays <= 0 || !formValues.window_size_days || !formValues.step_size_days) {
      setWindowCount(0);
      return;
    }

    // Calculate number of windows
    const windows = Math.floor((totalDays - formValues.window_size_days) / formValues.step_size_days) + 1;
    setWindowCount(Math.max(0, windows));
  };

  const calculateGridCombinations = () => {
    const enabledRanges = paramRanges.filter(param => param.enabled);
    if (enabledRanges.length === 0) {
      setGridCombinations(0);
      return;
    }
    
    let total = 1;
    enabledRanges.forEach(param => {
      total *= param.values.length;
    });
    
    setGridCombinations(total);
  };

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    
    let processedValue = value;
    if (type === 'number') {
      processedValue = value === '' ? '' : Number(value);
    }
    
    setFormValues(prev => ({
      ...prev,
      [name]: processedValue
    }));
    
    // Clear error when field is edited
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleSymbolsChange = (e) => {
    const symbolsString = e.target.value;
    const symbolsList = symbolsString.split(',').map(s => s.trim()).filter(s => s !== '');
    
    setFormValues(prev => ({
      ...prev,
      symbols: symbolsList
    }));
    
    if (errors.symbols) {
      setErrors(prev => ({ ...prev, symbols: null }));
    }
  };

  const handleParamToggle = (index) => {
    const updatedRanges = [...paramRanges];
    updatedRanges[index].enabled = !updatedRanges[index].enabled;
    setParamRanges(updatedRanges);
  };

  const handleParamValueChange = (paramIndex, valueIndex, newValue) => {
    const updatedRanges = [...paramRanges];
    
    // Handle different param types
    switch (updatedRanges[paramIndex].type) {
      case 'number':
        newValue = parseFloat(newValue);
        break;
      case 'integer':
        newValue = parseInt(newValue);
        break;
      case 'boolean':
        newValue = newValue === 'true';
        break;
    }
    
    updatedRanges[paramIndex].values[valueIndex] = newValue;
    setParamRanges(updatedRanges);
  };

  const handleAddParamValue = (paramIndex) => {
    const updatedRanges = [...paramRanges];
    const param = updatedRanges[paramIndex];
    
    // Add a reasonable step based on parameter type and existing values
    let newValue;
    switch (param.type) {
      case 'number':
        // For numbers, add a value that's 10% higher than the last value
        const lastVal = param.values[param.values.length - 1];
        newValue = Math.min(param.max || Infinity, lastVal * 1.1);
        break;
      case 'integer':
        // For integers, increment by 1
        newValue = Math.min(param.max || Infinity, param.values[param.values.length - 1] + 1);
        break;
      case 'boolean':
        // For booleans, toggle from last value
        newValue = !param.values[param.values.length - 1];
        break;
      default:
        // For strings, just duplicate the last value
        newValue = param.values[param.values.length - 1];
    }
    
    updatedRanges[paramIndex].values.push(newValue);
    setParamRanges(updatedRanges);
  };

  const handleRemoveParamValue = (paramIndex, valueIndex) => {
    const updatedRanges = [...paramRanges];
    if (updatedRanges[paramIndex].values.length > 1) {
      updatedRanges[paramIndex].values.splice(valueIndex, 1);
      setParamRanges(updatedRanges);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formValues.strategy_name) {
      newErrors.strategy_name = 'Strategy is required';
    }
    
    if (!formValues.symbols || formValues.symbols.length === 0) {
      newErrors.symbols = 'At least one symbol is required';
    }
    
    if (!formValues.start_date) {
      newErrors.start_date = 'Start date is required';
    }
    
    if (!formValues.end_date) {
      newErrors.end_date = 'End date is required';
    } else if (formValues.start_date && new Date(formValues.start_date) >= new Date(formValues.end_date)) {
      newErrors.end_date = 'End date must be after start date';
    }
    
    if (formValues.initial_balance <= 0) {
      newErrors.initial_balance = 'Initial balance must be greater than 0';
    }
    
    if (formValues.fee_rate < 0) {
      newErrors.fee_rate = 'Fee rate cannot be negative';
    }
    
    if (formValues.slippage < 0) {
      newErrors.slippage = 'Slippage cannot be negative';
    }
    
    if (formValues.risk_per_trade <= 0 || formValues.risk_per_trade > 1) {
      newErrors.risk_per_trade = 'Risk per trade must be between 0 and 1';
    }
    
    if (formValues.window_size_days <= 0) {
      newErrors.window_size_days = 'Window size must be greater than 0';
    }
    
    if (formValues.step_size_days <= 0) {
      newErrors.step_size_days = 'Step size must be greater than 0';
    }
    
    if (formValues.in_sample_pct <= 0 || formValues.in_sample_pct >= 1) {
      newErrors.in_sample_pct = 'In-sample percentage must be between 0 and 1';
    }
    
    // Check window count
    if (windowCount <= 0) {
      newErrors.window_count = 'Date range is too small for the window size and step size. Increase date range or reduce window/step size.';
    }
    
    // Check that at least one parameter is enabled for optimization
    const enabledParams = paramRanges.filter(param => param.enabled);
    if (enabledParams.length === 0) {
      newErrors.parameter_grid = 'At least one parameter must be enabled for optimization';
    }
    
    // Check that the total combinations doesn't exceed the limit
    if (gridCombinations > 1000) {
      newErrors.parameter_grid = `Too many parameter combinations: ${gridCombinations}. Maximum is 1000.`;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const buildParameterGrid = () => {
    const grid = {};
    
    paramRanges
      .filter(param => param.enabled)
      .forEach(param => {
        grid[param.name] = param.values;
      });
    
    return grid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Build the parameter grid
    const parameter_grid = buildParameterGrid();
    const updatedFormValues = {
      ...formValues,
      parameter_grid
    };
    
    setFormValues(updatedFormValues);
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    setIsSuccess(false);
    
    try {
      const response = await axios.post('/api/v1/backtesting/walk-forward', updatedFormValues);
      
      if (response.data && response.data.task_id) {
        setIsSuccess(true);
        if (onTaskCreated) {
          onTaskCreated(response.data);
        }
      }
    } catch (err) {
      console.error('Error creating walk-forward analysis task:', err);
      setErrors(prev => ({
        ...prev,
        form: err.response?.data?.detail || 'Failed to create walk-forward analysis task'
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFormValues(DEFAULT_FORM_VALUES);
    setErrors({});
    setIsSuccess(false);
    setParamRanges([]);
    setGridCombinations(0);
    setWindowCount(0);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {errors.form && (
        <div className="bg-red-50 p-4 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <ExclamationCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">{errors.form}</h3>
            </div>
          </div>
        </div>
      )}
      
      {isSuccess && (
        <div className="bg-green-50 p-4 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-5 w-5 text-green-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Walk-forward analysis task created successfully!</h3>
            </div>
          </div>
        </div>
      )}
      
      <div className="bg-blue-50 p-4 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <ArrowsRightLeftIcon className="h-5 w-5 text-blue-400" aria-hidden="true" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">About Walk-Forward Analysis</h3>
            <p className="mt-1 text-sm text-blue-700">
              Walk-forward analysis uses a sliding window approach to optimize parameters on in-sample 
              data and validate them on out-of-sample data, helping to test strategy robustness.
            </p>
            {windowCount > 0 && (
              <p className="mt-2 text-sm text-blue-700">
                Based on your settings, the analysis will include <strong>{windowCount}</strong> windows.
              </p>
            )}
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
        {/* Strategy Selection */}
        <div className="sm:col-span-3">
          <label htmlFor="strategy_name" className="block text-sm font-medium text-gray-700">
            Strategy <span className="text-red-500">*</span>
          </label>
          <div className="mt-1">
            <select
              id="strategy_name"
              name="strategy_name"
              value={formValues.strategy_name}
              onChange={handleChange}
              className={`
                block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                ${errors.strategy_name ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
              `}
            >
              <option value="">Select a strategy</option>
              {strategies.map(strategy => (
                <option key={strategy.name} value={strategy.name}>
                  {strategy.display_name || strategy.name}
                </option>
              ))}
            </select>
          </div>
          {errors.strategy_name && (
            <p className="mt-2 text-sm text-red-600" id="strategy-error">
              {errors.strategy_name}
            </p>
          )}
        </div>
        
        {/* Optimization Metric */}
        <div className="sm:col-span-3">
          <label htmlFor="optimization_metric" className="block text-sm font-medium text-gray-700">
            Optimization Metric
          </label>
          <div className="mt-1">
            <select
              id="optimization_metric"
              name="optimization_metric"
              value={formValues.optimization_metric}
              onChange={handleChange}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              {OPTIMIZATION_METRICS.map(metric => (
                <option key={metric.value} value={metric.value}>
                  {metric.label}
                </option>
              ))}
            </select>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Metric to maximize during in-sample optimization
          </p>
        </div>
        
        {/* Symbols */}
        <div className="sm:col-span-3">
          <label htmlFor="symbols" className="block text-sm font-medium text-gray-700">
            Symbols <span className="text-red-500">*</span>
          </label>
          <div className="mt-1">
            <input
              type="text"
              id="symbols"
              name="symbols"
              value={formValues.symbols.join(', ')}
              onChange={handleSymbolsChange}
              placeholder="BTC-USDT, ETH-USDT"
              className={`
                block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                ${errors.symbols ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
              `}
            />
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Comma-separated list of trading symbols
          </p>
          {errors.symbols && (
            <p className="mt-2 text-sm text-red-600" id="symbols-error">
              {errors.symbols}
            </p>
          )}
        </div>
        
        {/* Timeframe Selection */}
        <div className="sm:col-span-3">
          <label htmlFor="timeframe" className="block text-sm font-medium text-gray-700">
            Timeframe
          </label>
          <div className="mt-1">
            <select
              id="timeframe"
              name="timeframe"
              value={formValues.timeframe}
              onChange={handleChange}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              {TIMEFRAMES.map(tf => (
                <option key={tf.value} value={tf.value}>
                  {tf.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* Date Range */}
        <div className="sm:col-span-3">
          <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
            Start Date <span className="text-red-500">*</span>
          </label>
          <div className="mt-1 relative rounded-md shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <CalendarIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            </div>
            <input
              type="date"
              id="start_date"
              name="start_date"
              value={formValues.start_date}
              onChange={handleChange}
              className={`
                pl-10 block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                ${errors.start_date ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
              `}
            />
          </div>
          {errors.start_date && (
            <p className="mt-2 text-sm text-red-600" id="start-date-error">
              {errors.start_date}
            </p>
          )}
        </div>
        
        <div className="sm:col-span-3">
          <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
            End Date <span className="text-red-500">*</span>
          </label>
          <div className="mt-1 relative rounded-md shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <CalendarIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            </div>
            <input
              type="date"
              id="end_date"
              name="end_date"
              value={formValues.end_date}
              onChange={handleChange}
              className={`
                pl-10 block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                ${errors.end_date ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
              `}
            />
          </div>
          {errors.end_date && (
            <p className="mt-2 text-sm text-red-600" id="end-date-error">
              {errors.end_date}
            </p>
          )}
        </div>
        
        {/* Walk-Forward Settings */}
        <div className="sm:col-span-6">
          <div className="px-4 py-5 bg-gray-50 rounded-lg sm:p-6">
            <div className="md:grid md:grid-cols-3 md:gap-6">
              <div className="md:col-span-1">
                <h3 className="text-lg font-medium leading-6 text-gray-900">Walk-Forward Settings</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Configure the parameters for walk-forward analysis.
                </p>
                {errors.window_count && (
                  <div className="mt-4 rounded-md bg-red-50 p-2">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <ExclamationCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-red-600">{errors.window_count}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-5 md:mt-0 md:col-span-2">
                <div className="grid grid-cols-6 gap-6">
                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="window_size_days" className="block text-sm font-medium text-gray-700">
                      Window Size (days)
                    </label>
                    <input
                      type="number"
                      name="window_size_days"
                      id="window_size_days"
                      value={formValues.window_size_days}
                      onChange={handleChange}
                      min="1"
                      className={`
                        mt-1 block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                        ${errors.window_size_days ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
                      `}
                    />
                    {errors.window_size_days && (
                      <p className="mt-2 text-sm text-red-600">{errors.window_size_days}</p>
                    )}
                    <p className="mt-2 text-xs text-gray-500">
                      Size of each analysis window
                    </p>
                  </div>
                  
                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="step_size_days" className="block text-sm font-medium text-gray-700">
                      Step Size (days)
                    </label>
                    <input
                      type="number"
                      name="step_size_days"
                      id="step_size_days"
                      value={formValues.step_size_days}
                      onChange={handleChange}
                      min="1"
                      className={`
                        mt-1 block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                        ${errors.step_size_days ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
                      `}
                    />
                    {errors.step_size_days && (
                      <p className="mt-2 text-sm text-red-600">{errors.step_size_days}</p>
                    )}
                    <p className="mt-2 text-xs text-gray-500">
                      Days to advance for each new window
                    </p>
                  </div>
                  
                  <div className="col-span-6">
                    <label htmlFor="in_sample_pct" className="block text-sm font-medium text-gray-700">
                      In-Sample Percentage
                    </label>
                    <input
                      type="number"
                      name="in_sample_pct"
                      id="in_sample_pct"
                      value={formValues.in_sample_pct}
                      onChange={handleChange}
                      min="0.1"
                      max="0.9"
                      step="0.05"
                      className={`
                        mt-1 block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                        ${errors.in_sample_pct ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
                      `}
                    />
                    {errors.in_sample_pct && (
                      <p className="mt-2 text-sm text-red-600">{errors.in_sample_pct}</p>
                    )}
                    <p className="mt-2 text-xs text-gray-500">
                      Fraction of each window used for parameter optimization (e.g., 0.7 for 70%)
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Initial Balance */}
        <div className="sm:col-span-2">
          <label htmlFor="initial_balance" className="block text-sm font-medium text-gray-700">
            Initial Balance
          </label>
          <div className="mt-1 relative rounded-md shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-500 sm:text-sm">$</span>
            </div>
            <input
              type="number"
              id="initial_balance"
              name="initial_balance"
              value={formValues.initial_balance}
              onChange={handleChange}
              min="0"
              step="1000"
              className={`
                pl-7 block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                ${errors.initial_balance ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
              `}
            />
          </div>
          {errors.initial_balance && (
            <p className="mt-2 text-sm text-red-600" id="balance-error">
              {errors.initial_balance}
            </p>
          )}
        </div>
        
        {/* Fee Rate */}
        <div className="sm:col-span-2">
          <label htmlFor="fee_rate" className="block text-sm font-medium text-gray-700">
            Fee Rate
          </label>
          <div className="mt-1 relative rounded-md shadow-sm">
            <input
              type="number"
              id="fee_rate"
              name="fee_rate"
              value={formValues.fee_rate}
              onChange={handleChange}
              min="0"
              step="0.0001"
              className={`
                block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                ${errors.fee_rate ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
              `}
            />
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <span className="text-gray-500 sm:text-sm">%</span>
            </div>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Exchange fee rate (e.g., 0.0004 for 0.04%)
          </p>
          {errors.fee_rate && (
            <p className="mt-2 text-sm text-red-600" id="fee-error">
              {errors.fee_rate}
            </p>
          )}
        </div>
        
        {/* Slippage and Risk Per Trade */}
        <div className="sm:col-span-1">
          <label htmlFor="slippage" className="block text-sm font-medium text-gray-700">
            Slippage
          </label>
          <div className="mt-1 relative rounded-md shadow-sm">
            <input
              type="number"
              id="slippage"
              name="slippage"
              value={formValues.slippage}
              onChange={handleChange}
              min="0"
              step="0.0001"
              className={`
                block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                ${errors.slippage ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
              `}
            />
          </div>
          {errors.slippage && (
            <p className="mt-2 text-sm text-red-600" id="slippage-error">
              {errors.slippage}
            </p>
          )}
        </div>
        
        <div className="sm:col-span-1">
          <label htmlFor="risk_per_trade" className="block text-sm font-medium text-gray-700">
            Risk Per Trade
          </label>
          <div className="mt-1 relative rounded-md shadow-sm">
            <input
              type="number"
              id="risk_per_trade"
              name="risk_per_trade"
              value={formValues.risk_per_trade}
              onChange={handleChange}
              min="0.001"
              max="1"
              step="0.01"
              className={`
                block w-full rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                ${errors.risk_per_trade ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
              `}
            />
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Fraction of account (0-1)
          </p>
          {errors.risk_per_trade && (
            <p className="mt-2 text-sm text-red-600" id="risk-error">
              {errors.risk_per_trade}
            </p>
          )}
        </div>
        
        {/* Parameter Grid Configuration */}
        {paramRanges.length > 0 && (
          <div className="sm:col-span-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-gray-900">Parameter Grid</h3>
              <div className="flex items-center">
                <BeakerIcon className="h-5 w-5 text-gray-500 mr-1" />
                <span className={`text-sm ${gridCombinations > 1000 ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                  {gridCombinations} combinations
                </span>
              </div>
            </div>
            {errors.parameter_grid && (
              <div className="mb-3 rounded-md bg-red-50 p-2">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <ExclamationCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-600">{errors.parameter_grid}</p>
                  </div>
                </div>
              </div>
            )}
            <p className="text-sm text-gray-500 mb-3">
              Enable parameters to optimize and specify values to test for each parameter.
            </p>
            <div className="bg-gray-100 p-4 rounded-md">
              <div className="space-y-4">
                {paramRanges.map((param, paramIndex) => (
                  <div key={param.name} className="rounded-md border border-gray-300 bg-white p-3">
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id={`param-${param.name}`}
                          checked={param.enabled}
                          onChange={() => handleParamToggle(paramIndex)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor={`param-${param.name}`} className="ml-2 block text-sm font-medium text-gray-700">
                          {param.name.replace(/_/g, ' ')}
                        </label>
                        {param.description && (
                          <span className="ml-2 text-xs text-gray-500">{param.description}</span>
                        )}
                      </div>
                      {param.enabled && (
                        <button
                          type="button"
                          onClick={() => handleAddParamValue(paramIndex)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Add value"
                        >
                          <PlusIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                    {param.enabled && (
                      <div className="pl-6">
                        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                          {param.values.map((value, valueIndex) => (
                            <div key={valueIndex} className="flex items-center">
                              <input
                                type={param.type === 'boolean' ? 'checkbox' : 'text'}
                                value={param.type === 'boolean' ? (value ? 'true' : 'false') : value}
                                checked={param.type === 'boolean' ? value : undefined}
                                onChange={(e) => handleParamValueChange(
                                  paramIndex, 
                                  valueIndex, 
                                  param.type === 'boolean' ? e.target.checked : e.target.value
                                )}
                                className={`
                                  ${param.type === 'boolean' ? 'h-4 w-4 rounded' : 'w-full rounded-md py-1 px-2 text-sm'} 
                                  border-gray-300 focus:border-blue-500 focus:ring-blue-500
                                `}
                              />
                              {param.values.length > 1 && (
                                <button
                                  type="button"
                                  onClick={() => handleRemoveParamValue(paramIndex, valueIndex)}
                                  className="ml-2 text-red-500 hover:text-red-700"
                                  title="Remove value"
                                >
                                  <MinusIcon className="h-4 w-4" />
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={handleReset}
          className="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Reset
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 flex items-center"
        >
          {isLoading && <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />}
          Run Walk-Forward Analysis
        </button>
      </div>
    </form>
  );
}

export default WalkForwardForm; 