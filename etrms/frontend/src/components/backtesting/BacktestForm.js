import React, { useState } from 'react';
import axios from 'axios';
import { 
  ArrowPathIcon, 
  CalendarIcon, 
  ChartBarIcon,
  ExclamationCircleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const DEFAULT_FORM_VALUES = {
  strategy_name: '',
  symbols: ['BTC-USDT'],
  timeframe: '1h',
  start_date: '',
  end_date: '',
  initial_balance: 10000,
  fee_rate: 0.0004,
  slippage: 0.0001,
  risk_per_trade: 0.01,
  name: '',
  description: '',
  strategy_params: {}
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

function BacktestForm({ strategies = [], onTaskCreated }) {
  const [formValues, setFormValues] = useState(DEFAULT_FORM_VALUES);
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [paramFields, setParamFields] = useState([]);

  // Update strategy parameters based on selected strategy
  const updateStrategyParams = (strategyName) => {
    const strategy = strategies.find(s => s.name === strategyName);
    if (strategy && strategy.parameters) {
      // Initialize parameter fields with default values
      const initialParams = {};
      const fields = [];
      
      Object.entries(strategy.parameters).forEach(([key, param]) => {
        initialParams[key] = param.default;
        fields.push({
          name: key,
          type: param.type,
          default: param.default,
          description: param.description || '',
          min: param.min,
          max: param.max
        });
      });
      
      setFormValues(prev => ({
        ...prev,
        strategy_params: initialParams
      }));
      
      setParamFields(fields);
    } else {
      setFormValues(prev => ({
        ...prev,
        strategy_params: {}
      }));
      setParamFields([]);
    }
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
    
    // Special case for strategy_name to update parameters
    if (name === 'strategy_name') {
      updateStrategyParams(value);
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

  const handleStrategyParamChange = (e) => {
    const { name, value, type } = e.target;
    
    let processedValue = value;
    if (type === 'number') {
      processedValue = value === '' ? '' : Number(value);
    } else if (type === 'checkbox') {
      processedValue = e.target.checked;
    }
    
    setFormValues(prev => ({
      ...prev,
      strategy_params: {
        ...prev.strategy_params,
        [name]: processedValue
      }
    }));
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
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    setIsSuccess(false);
    
    try {
      const response = await axios.post('/api/v1/backtesting/tasks', formValues);
      
      if (response.data && response.data.id) {
        setIsSuccess(true);
        if (onTaskCreated) {
          onTaskCreated(response.data);
        }
        
        // Optionally, reset form or show success message
        // setFormValues(DEFAULT_FORM_VALUES);
      }
    } catch (err) {
      console.error('Error creating backtest task:', err);
      setErrors(prev => ({
        ...prev,
        form: err.response?.data?.detail || 'Failed to create backtest task'
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFormValues(DEFAULT_FORM_VALUES);
    setErrors({});
    setIsSuccess(false);
    setParamFields([]);
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
              <h3 className="text-sm font-medium text-green-800">Backtest task created successfully!</h3>
            </div>
          </div>
        </div>
      )}
      
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
                block w-full rounded-md shadow-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                ${errors.strategy_name ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500' : ''}
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
        
        {/* Name (Optional) */}
        <div className="sm:col-span-3">
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Task Name (Optional)
          </label>
          <div className="mt-1">
            <input
              type="text"
              id="name"
              name="name"
              value={formValues.name}
              onChange={handleChange}
              placeholder="My Backtest"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
          </div>
        </div>
        
        {/* Symbols */}
        <div className="sm:col-span-6">
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
        <div className="sm:col-span-2">
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
        <div className="sm:col-span-2">
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
        
        <div className="sm:col-span-2">
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
        
        {/* Slippage */}
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
        
        {/* Risk Per Trade */}
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
        
        {/* Description (Optional) */}
        <div className="sm:col-span-6">
          <label htmlFor="description" className="block text-sm font-medium text-gray-700">
            Description (Optional)
          </label>
          <div className="mt-1">
            <textarea
              id="description"
              name="description"
              rows={3}
              value={formValues.description}
              onChange={handleChange}
              placeholder="Notes about this backtest"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
          </div>
        </div>
        
        {/* Strategy Parameters */}
        {paramFields.length > 0 && (
          <div className="sm:col-span-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Strategy Parameters</h3>
            <div className="bg-gray-100 p-4 rounded-md">
              <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                {paramFields.map(field => (
                  <div key={field.name} className="sm:col-span-2">
                    <label htmlFor={field.name} className="block text-sm font-medium text-gray-700">
                      {field.name.replace(/_/g, ' ')}
                    </label>
                    <div className="mt-1">
                      {field.type === 'boolean' ? (
                        <input
                          type="checkbox"
                          id={field.name}
                          name={field.name}
                          checked={formValues.strategy_params[field.name] || false}
                          onChange={handleStrategyParamChange}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      ) : field.type === 'select' && field.options ? (
                        <select
                          id={field.name}
                          name={field.name}
                          value={formValues.strategy_params[field.name] || ''}
                          onChange={handleStrategyParamChange}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        >
                          {field.options.map(option => (
                            <option key={option.value} value={option.value}>
                              {option.label || option.value}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type={field.type === 'number' ? 'number' : 'text'}
                          id={field.name}
                          name={field.name}
                          value={formValues.strategy_params[field.name] ?? ''}
                          onChange={handleStrategyParamChange}
                          min={field.min}
                          max={field.max}
                          step={field.type === 'number' ? (field.step || (field.max && field.max < 1 ? 0.01 : 1)) : undefined}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        />
                      )}
                    </div>
                    {field.description && (
                      <p className="mt-1 text-xs text-gray-500">{field.description}</p>
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
          Create Task
        </button>
      </div>
    </form>
  );
}

export default BacktestForm; 