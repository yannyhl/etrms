import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ArrowPathIcon, 
  ExclamationCircleIcon,
  InformationCircleIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import { 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ZAxis,
  Legend,
  Cell
} from 'recharts';

function OptimizationResults({ selectedTask }) {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedParamX, setSelectedParamX] = useState('');
  const [selectedParamY, setSelectedParamY] = useState('');
  const [availableParams, setAvailableParams] = useState([]);
  const [showAllResults, setShowAllResults] = useState(false);
  const [sortMetric, setSortMetric] = useState('');
  const [sortDirection, setSortDirection] = useState('desc');

  useEffect(() => {
    if (selectedTask && selectedTask.id && selectedTask.task_type === 'optimization') {
      fetchResults(selectedTask.id);
    } else {
      setResults(null);
    }
  }, [selectedTask]);

  useEffect(() => {
    if (results && results.all_results && results.all_results.length > 0) {
      // Extract parameter names from first result
      const firstResult = results.all_results[0];
      const paramNames = Object.keys(firstResult.params || {});
      setAvailableParams(paramNames);
      
      // Set initial X and Y axis parameters if available
      if (paramNames.length >= 2) {
        setSelectedParamX(paramNames[0]);
        setSelectedParamY(paramNames[1]);
      } else if (paramNames.length === 1) {
        setSelectedParamX(paramNames[0]);
        setSelectedParamY('');
      }
      
      // Set initial sort metric
      const metricsKeys = Object.keys(firstResult.metrics || {});
      if (metricsKeys.length > 0) {
        setSortMetric(metricsKeys[0]);
      }
    }
  }, [results]);

  const fetchResults = async (taskId) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`/api/v1/backtesting/optimize/results/${taskId}`);
      setResults(response.data);
    } catch (err) {
      console.error('Error fetching optimization results:', err);
      setError('Failed to load optimization results. Please try again later.');
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

  const prepareScatterData = () => {
    if (!results || !results.all_results || !selectedParamX) {
      return [];
    }
    
    return results.all_results.map((result, index) => {
      const data = {
        name: `Run ${index + 1}`,
        x: result.params[selectedParamX],
        y: selectedParamY ? result.params[selectedParamY] : 0,
        z: result.metrics[sortMetric] || 0,
        ...result.metrics
      };
      
      // Include a synthetic "rank" for coloring
      data.rank = results.all_results.findIndex(r => 
        r.metrics[sortMetric] === result.metrics[sortMetric]
      ) + 1;
      
      return data;
    });
  };

  const handleSort = (metric) => {
    if (sortMetric === metric) {
      // Toggle direction if same metric
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new metric and default to descending
      setSortMetric(metric);
      setSortDirection('desc');
    }
  };

  const getSortedResults = () => {
    if (!results || !results.all_results) return [];
    
    return [...results.all_results].sort((a, b) => {
      const aValue = a.metrics[sortMetric] || 0;
      const bValue = b.metrics[sortMetric] || 0;
      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
    });
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

  if (!selectedTask) {
    return (
      <div className="flex items-center justify-center h-64 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <div className="text-gray-500">
          <InformationCircleIcon className="h-10 w-10 mx-auto mb-2" />
          <p>Select an optimization task from the Tasks tab to view results</p>
        </div>
      </div>
    );
  }

  if (selectedTask.task_type !== 'optimization') {
    return (
      <div className="flex items-center justify-center h-64 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <div className="text-gray-500">
          <InformationCircleIcon className="h-10 w-10 mx-auto mb-2" />
          <p>Selected task is not a parameter optimization task</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <ArrowPathIcon className="h-8 w-8 text-blue-500 animate-spin" />
        <span className="ml-2 text-gray-600">Loading optimization results...</span>
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

  if (!results || !results.all_results || results.all_results.length === 0) {
    return (
      <div className="text-center py-10 bg-gray-100 rounded-lg">
        <p className="text-gray-600">
          {selectedTask.status === 'completed' 
            ? 'No optimization results available.'
            : `Task status: ${selectedTask.status}. Wait for optimization to complete.`}
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

  const scatterData = prepareScatterData();
  const sortedResults = getSortedResults();
  const displayedResults = showAllResults ? sortedResults : sortedResults.slice(0, 10);

  return (
    <div className="space-y-6">
      {/* Best Parameters Summary */}
      <div className="bg-white p-4 rounded-lg shadow border">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Optimization Results</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Best Parameters</h4>
            <div className="bg-gray-50 rounded-md p-3">
              {results.best_params && Object.entries(results.best_params).map(([param, value]) => (
                <div key={param} className="flex justify-between py-1">
                  <span className="text-sm text-gray-600">{param}:</span>
                  <span className="text-sm font-medium">{value}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Best Performance</h4>
            <div className="bg-gray-50 rounded-md p-3">
              {results.best_metrics && Object.entries(results.best_metrics).slice(0, 6).map(([metric, value]) => (
                <div key={metric} className="flex justify-between py-1">
                  <span className="text-sm text-gray-600">{metric.replace(/_/g, ' ')}:</span>
                  <span className="text-sm font-medium">{renderMetricValue(value, metric)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Visualization */}
      {availableParams.length > 0 && (
        <div className="bg-white p-4 rounded-lg shadow border">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Parameter Visualization</h3>
          
          <div className="flex flex-wrap gap-4 mb-4">
            <div>
              <label htmlFor="param-x" className="block text-sm font-medium text-gray-700 mb-1">
                X-Axis Parameter
              </label>
              <select
                id="param-x"
                value={selectedParamX}
                onChange={(e) => setSelectedParamX(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                {availableParams.map(param => (
                  <option key={param} value={param}>{param}</option>
                ))}
              </select>
            </div>
            
            {availableParams.length > 1 && (
              <div>
                <label htmlFor="param-y" className="block text-sm font-medium text-gray-700 mb-1">
                  Y-Axis Parameter
                </label>
                <select
                  id="param-y"
                  value={selectedParamY}
                  onChange={(e) => setSelectedParamY(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="">None</option>
                  {availableParams.map(param => (
                    param !== selectedParamX && <option key={param} value={param}>{param}</option>
                  ))}
                </select>
              </div>
            )}
            
            <div>
              <label htmlFor="color-metric" className="block text-sm font-medium text-gray-700 mb-1">
                Color By Metric
              </label>
              <select
                id="color-metric"
                value={sortMetric}
                onChange={(e) => setSortMetric(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                {results.all_results[0] && Object.keys(results.all_results[0].metrics).map(metric => (
                  <option key={metric} value={metric}>{metric.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart
                margin={{
                  top: 20,
                  right: 20,
                  bottom: 50,
                  left: 30,
                }}
              >
                <CartesianGrid />
                <XAxis 
                  type="number" 
                  dataKey="x" 
                  name={selectedParamX} 
                  label={{ 
                    value: selectedParamX, 
                    position: 'bottom',
                    style: { textAnchor: 'middle' }
                  }} 
                />
                
                {selectedParamY && (
                  <YAxis 
                    type="number" 
                    dataKey="y" 
                    name={selectedParamY} 
                    label={{ 
                      value: selectedParamY, 
                      angle: -90, 
                      position: 'left',
                      style: { textAnchor: 'middle' }
                    }} 
                  />
                )}
                
                <ZAxis type="number" dataKey="z" range={[50, 400]} />
                <Tooltip 
                  formatter={(value, name, props) => {
                    // Format different metrics appropriately
                    if (name === 'x') return [value, selectedParamX];
                    if (name === 'y') return [value, selectedParamY];
                    if (name === 'z') return [renderMetricValue(value, sortMetric), sortMetric];
                    
                    // For other metrics that appear in the tooltip
                    return [renderMetricValue(value, name), name.replace(/_/g, ' ')];
                  }}
                  itemSorter={(item) => {
                    // Show x and y first, then the selected metric, then others
                    if (item.name === 'x') return -3;
                    if (item.name === 'y') return -2;
                    if (item.name === 'z') return -1;
                    return 0;
                  }}
                />
                <Legend />
                <Scatter name={sortMetric} data={scatterData} fill="#8884d8">
                  {scatterData.map((entry, index) => {
                    // Calculate color based on rank (higher rank = better performance)
                    const total = scatterData.length;
                    const percentile = entry.rank / total;
                    
                    // Create a color gradient from red (worst) to green (best)
                    const r = Math.floor(255 * percentile);
                    const g = Math.floor(255 * (1 - percentile));
                    const b = 50;
                    
                    return <Cell key={`cell-${index}`} fill={`rgb(${r}, ${g}, ${b})`} />;
                  })}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Results Table */}
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Parameter Combinations</h3>
          <button 
            className="flex items-center text-sm text-blue-600 hover:text-blue-800"
            onClick={() => setShowAllResults(!showAllResults)}
          >
            {showAllResults ? (
              <>
                <FunnelIcon className="h-4 w-4 mr-1" />
                Show Top 10
              </>
            ) : (
              <>
                <ChevronDownIcon className="h-4 w-4 mr-1" />
                Show All ({results.all_results.length})
              </>
            )}
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                {/* Parameter Columns */}
                {availableParams.map(param => (
                  <th 
                    key={param} 
                    scope="col" 
                    className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {param}
                  </th>
                ))}
                {/* Metrics Columns */}
                {results.all_results[0] && Object.keys(results.all_results[0].metrics).map(metric => (
                  <th 
                    key={metric} 
                    scope="col" 
                    className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort(metric)}
                  >
                    <div className="flex items-center">
                      <span>{metric.replace(/_/g, ' ')}</span>
                      {sortMetric === metric && (
                        <span className="ml-1">
                          {sortDirection === 'desc' ? '▼' : '▲'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayedResults.map((result, idx) => (
                <tr key={idx} className={idx === 0 && sortMetric === results.optimization_metric ? 'bg-green-50' : 'hover:bg-gray-50'}>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                    {idx + 1}
                  </td>
                  {/* Parameter Values */}
                  {availableParams.map(param => (
                    <td key={param} className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                      {result.params[param]}
                    </td>
                  ))}
                  {/* Metric Values */}
                  {Object.entries(result.metrics).map(([metric, value]) => (
                    <td 
                      key={metric} 
                      className={`px-3 py-2 whitespace-nowrap text-sm ${
                        sortMetric === metric ? 'font-medium' : ''
                      } ${
                        idx === 0 && metric === results.optimization_metric ? 'text-green-600 font-medium' : 'text-gray-500'
                      }`}
                    >
                      {renderMetricValue(value, metric)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {!showAllResults && results.all_results.length > 10 && (
          <div className="mt-4 text-center">
            <button 
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center mx-auto"
              onClick={() => setShowAllResults(true)}
            >
              <ChevronDownIcon className="h-4 w-4 mr-1" />
              Show All {results.all_results.length} Results
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default OptimizationResults; 