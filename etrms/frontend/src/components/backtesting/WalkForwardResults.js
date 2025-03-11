import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ArrowPathIcon, 
  ExclamationCircleIcon,
  InformationCircleIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  ArrowsRightLeftIcon
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
  ComposedChart,
  Bar,
  Scatter,
  Area
} from 'recharts';

function WalkForwardResults({ selectedTask }) {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('return_percentage');
  const [showDetailedWindows, setShowDetailedWindows] = useState(false);

  useEffect(() => {
    if (selectedTask && selectedTask.id && selectedTask.task_type === 'walk_forward') {
      fetchResults(selectedTask.id);
    } else {
      setResults(null);
    }
  }, [selectedTask]);

  const fetchResults = async (taskId) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`/api/v1/backtesting/walk-forward/results/${taskId}`);
      setResults(response.data);
      
      // Set a default metric if available
      if (response.data && response.data.combined_metrics) {
        const availableMetrics = Object.keys(response.data.combined_metrics);
        if (availableMetrics.includes('return_percentage')) {
          setSelectedMetric('return_percentage');
        } else if (availableMetrics.includes('sharpe_ratio')) {
          setSelectedMetric('sharpe_ratio');
        } else if (availableMetrics.length > 0) {
          setSelectedMetric(availableMetrics[0]);
        }
      }
    } catch (err) {
      console.error('Error fetching walk-forward results:', err);
      setError('Failed to load walk-forward analysis results. Please try again later.');
    } finally {
      setIsLoading(false);
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
    return new Date(dateString).toLocaleDateString();
  };

  const renderMetricValue = (value, metricName) => {
    if (value === undefined || value === null) return 'N/A';
    
    // Format based on metric type
    if (metricName.includes('percentage') || 
        metricName.includes('drawdown') || 
        metricName.includes('win_rate')) {
      return formatPercentage(value);
    } else if (metricName.includes('balance') || 
              metricName.includes('profit') || 
              metricName.includes('pnl')) {
      return formatCurrency(value);
    } else {
      return formatNumber(value);
    }
  };

  const prepareWindowsChart = () => {
    if (!results || !results.windows) return [];
    
    return results.windows.map((window, index) => ({
      index: index + 1,
      name: `Window ${index + 1}`,
      start: formatDate(window.start_date),
      end: formatDate(window.end_date),
      in_sample: window.in_sample_metrics[selectedMetric] || 0,
      out_sample: window.out_sample_metrics[selectedMetric] || 0
    }));
  };

  const prepareParameterEvolutionData = () => {
    if (!results || !results.windows) return [];
    
    // Extract parameters from the first window to know what to track
    const firstWindow = results.windows[0];
    if (!firstWindow || !firstWindow.optimized_params) return [];
    
    const paramNames = Object.keys(firstWindow.optimized_params);
    
    return results.windows.map((window, index) => {
      const data = {
        index: index + 1,
        name: `Window ${index + 1}`
      };
      
      // Add all parameters
      paramNames.forEach(param => {
        data[param] = window.optimized_params[param];
      });
      
      // Add performance metrics for coloring/sizing
      data.performance = window.out_sample_metrics[selectedMetric] || 0;
      
      return data;
    });
  };

  const getParamLineColors = () => {
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00c49f'];
    const firstWindow = results?.windows?.[0];
    if (!firstWindow || !firstWindow.optimized_params) return {};
    
    const paramNames = Object.keys(firstWindow.optimized_params);
    
    return paramNames.reduce((acc, param, index) => {
      acc[param] = colors[index % colors.length];
      return acc;
    }, {});
  };

  if (!selectedTask) {
    return (
      <div className="flex items-center justify-center h-64 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <div className="text-gray-500">
          <InformationCircleIcon className="h-10 w-10 mx-auto mb-2" />
          <p>Select a walk-forward analysis task from the Tasks tab to view results</p>
        </div>
      </div>
    );
  }

  if (selectedTask.task_type !== 'walk_forward') {
    return (
      <div className="flex items-center justify-center h-64 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <div className="text-gray-500">
          <InformationCircleIcon className="h-10 w-10 mx-auto mb-2" />
          <p>Selected task is not a walk-forward analysis task</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <ArrowPathIcon className="h-8 w-8 text-blue-500 animate-spin" />
        <span className="ml-2 text-gray-600">Loading walk-forward analysis results...</span>
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

  if (!results || !results.windows || results.windows.length === 0) {
    return (
      <div className="text-center py-10 bg-gray-100 rounded-lg">
        <p className="text-gray-600">
          {selectedTask.status === 'completed' 
            ? 'No walk-forward analysis results available.'
            : `Task status: ${selectedTask.status}. Wait for analysis to complete.`}
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

  const windowsChartData = prepareWindowsChart();
  const paramEvolutionData = prepareParameterEvolutionData();
  const paramLineColors = getParamLineColors();
  const paramNames = Object.keys(paramLineColors);

  return (
    <div className="space-y-6">
      {/* Combined Results Summary */}
      <div className="bg-white p-4 rounded-lg shadow border">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Walk-Forward Analysis Results</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Analysis Overview</h4>
            <div className="bg-gray-50 rounded-md p-3">
              <div className="flex justify-between py-1">
                <span className="text-sm text-gray-600">Total Windows:</span>
                <span className="text-sm font-medium">{results.windows.length}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-sm text-gray-600">Start Date:</span>
                <span className="text-sm font-medium">{formatDate(results.windows[0]?.start_date)}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-sm text-gray-600">End Date:</span>
                <span className="text-sm font-medium">{formatDate(results.windows[results.windows.length - 1]?.end_date)}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-sm text-gray-600">Window Size:</span>
                <span className="text-sm font-medium">{results.window_size_days} days</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-sm text-gray-600">Step Size:</span>
                <span className="text-sm font-medium">{results.step_size_days} days</span>
              </div>
            </div>
          </div>
          
          <div className="space-y-3 md:col-span-2">
            <h4 className="text-sm font-medium text-gray-700">Combined Out-of-Sample Performance</h4>
            <div className="bg-gray-50 rounded-md p-3">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {results.combined_metrics && Object.entries(results.combined_metrics).map(([metric, value]) => (
                  <div key={metric} className="flex flex-col justify-between py-1">
                    <span className="text-xs text-gray-500">{metric.replace(/_/g, ' ')}</span>
                    <span className="text-sm font-medium">{renderMetricValue(value, metric)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Visualization */}
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Window Performance Comparison</h3>
          <div>
            <label htmlFor="selected-metric" className="text-sm font-medium text-gray-700 mr-2">
              Metric:
            </label>
            <select
              id="selected-metric"
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              {results.windows[0]?.in_sample_metrics && Object.keys(results.windows[0].in_sample_metrics).map(metric => (
                <option key={metric} value={metric}>
                  {metric.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={windowsChartData}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 10,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="index" />
              <YAxis 
                label={{ 
                  value: selectedMetric.replace(/_/g, ' '), 
                  angle: -90, 
                  position: 'insideLeft' 
                }} 
              />
              <Tooltip 
                formatter={(value, name) => {
                  return [
                    renderMetricValue(value, selectedMetric), 
                    name === 'in_sample' ? 'In-Sample' : 'Out-of-Sample'
                  ];
                }}
                labelFormatter={(value) => `Window ${value}`}
              />
              <Legend />
              <Bar 
                dataKey="in_sample" 
                fill="#8884d8" 
                name="In-Sample" 
              />
              <Line 
                type="monotone" 
                dataKey="out_sample" 
                stroke="#ff7300" 
                name="Out-of-Sample" 
                dot={{ stroke: '#ff7300', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Parameter Evolution */}
      <div className="bg-white p-4 rounded-lg shadow border">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Parameter Evolution</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={paramEvolutionData}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 10,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="index" />
              <YAxis />
              <Tooltip 
                formatter={(value, name, props) => {
                  if (paramNames.includes(name)) {
                    return [value, name.replace(/_/g, ' ')];
                  }
                  return [value, name];
                }}
                labelFormatter={(value) => `Window ${value}`}
              />
              <Legend />
              {paramNames.map(param => (
                <Line 
                  key={param}
                  type="monotone" 
                  dataKey={param} 
                  stroke={paramLineColors[param]} 
                  name={param.replace(/_/g, ' ')}
                  dot={{ stroke: paramLineColors[param], strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Windows Detail */}
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Window Details</h3>
          <button 
            className="flex items-center text-sm text-blue-600 hover:text-blue-800"
            onClick={() => setShowDetailedWindows(!showDetailedWindows)}
          >
            {showDetailedWindows ? (
              <>
                <ChevronRightIcon className="h-4 w-4 mr-1" />
                Hide Details
              </>
            ) : (
              <>
                <ChevronDownIcon className="h-4 w-4 mr-1" />
                Show Details
              </>
            )}
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Window
                </th>
                <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date Range
                </th>
                <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  In-Sample {selectedMetric.replace(/_/g, ' ')}
                </th>
                <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Out-of-Sample {selectedMetric.replace(/_/g, ' ')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.windows.map((window, index) => (
                <React.Fragment key={index}>
                  <tr className="hover:bg-gray-50 cursor-pointer" onClick={() => showDetailedWindows ? null : setShowDetailedWindows(true)}>
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                      Window {index + 1}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(window.start_date)} - {formatDate(window.end_date)}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                      {renderMetricValue(window.in_sample_metrics[selectedMetric], selectedMetric)}
                    </td>
                    <td className={`px-3 py-2 whitespace-nowrap text-sm font-medium ${
                      window.out_sample_metrics[selectedMetric] > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {renderMetricValue(window.out_sample_metrics[selectedMetric], selectedMetric)}
                    </td>
                  </tr>
                  
                  {/* Expanded details */}
                  {showDetailedWindows && (
                    <tr className="bg-gray-50">
                      <td colSpan={4} className="px-3 py-2">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-2">
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 mb-2">Optimized Parameters</h4>
                            <div className="grid grid-cols-2 gap-2">
                              {window.optimized_params && Object.entries(window.optimized_params).map(([param, value]) => (
                                <div key={param} className="flex justify-between py-1 border-b border-gray-200">
                                  <span className="text-sm text-gray-600">{param.replace(/_/g, ' ')}:</span>
                                  <span className="text-sm font-medium">{value}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 mb-2">Performance Metrics</h4>
                            <div className="grid grid-cols-2 gap-2">
                              {window.out_sample_metrics && Object.entries(window.out_sample_metrics).map(([metric, value]) => (
                                <div key={metric} className="flex justify-between py-1 border-b border-gray-200">
                                  <span className="text-sm text-gray-600">{metric.replace(/_/g, ' ')}:</span>
                                  <span className="text-sm font-medium">{renderMetricValue(value, metric)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default WalkForwardResults; 