import { useState, useEffect } from 'react';
import axios from 'axios';
import { ChartBarIcon, ArrowTrendingDownIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';
import useWebSocket from '../hooks/useWebSocket';
import { Channels } from '../services/websocket';
import WebSocketStatus from '../components/WebSocketStatus';

export default function Positions() {
  const [positions, setPositions] = useState([]);
  const [positionsBySymbol, setPositionsBySymbol] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'by-symbol', 'by-exchange'
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [selectedExchange, setSelectedExchange] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // WebSocket connection for real-time position data
  const { 
    data: positionsData, 
    status: positionsStatus, 
    isConnected: isPositionsConnected,
    connect: connectPositionsWs,
    error: positionsError
  } = useWebSocket(Channels.POSITIONS);

  // Update positions when received from WebSocket
  useEffect(() => {
    if (positionsData) {
      // Update positions state from WebSocket data
      const allPositions = [];
      
      // If data includes position_summary property from API format
      if (positionsData.data && positionsData.data.exchanges) {
        // Format from API response
        const data = positionsData.data;
        setPositionsBySymbol(data.positions_by_symbol || {});
        
        // Extract all positions into a flat array
        Object.entries(data.exchanges || {}).forEach(([exchangeName, exchangeData]) => {
          (exchangeData.positions || []).forEach(position => {
            allPositions.push({
              ...position,
              exchange: exchangeName
            });
          });
        });
      } else if (positionsData.exchanges) {
        // Format from direct WebSocket
        setPositionsBySymbol(positionsData.positions_by_symbol || {});
        
        // Extract all positions into a flat array
        Object.entries(positionsData.exchanges || {}).forEach(([exchangeName, exchangeData]) => {
          (exchangeData.positions || []).forEach(position => {
            allPositions.push({
              ...position,
              exchange: exchangeName
            });
          });
        });
      }
      
      setPositions(allPositions);
      setLoading(false);
    }
  }, [positionsData]);

  // Fetch positions data initially or when WebSocket is not connected
  useEffect(() => {
    if (!isPositionsConnected) {
      fetchPositions();
    }
  }, [isPositionsConnected]);

  const fetchPositions = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/positions');
      if (response.data.status === 'success' && response.data.data) {
        const data = response.data.data;
        setPositionsBySymbol(data.positions_by_symbol || {});
        
        // Extract all positions into a flat array
        const allPositions = [];
        Object.entries(data.exchanges || {}).forEach(([exchangeName, exchangeData]) => {
          (exchangeData.positions || []).forEach(position => {
            allPositions.push({
              ...position,
              exchange: exchangeName
            });
          });
        });
        
        setPositions(allPositions);
        setError(null);
      } else {
        setError(response.data.message || 'Failed to fetch positions');
      }
    } catch (err) {
      console.error('Error fetching positions:', err);
      setError('Failed to fetch positions data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const analyzePosition = async (symbol, exchange) => {
    setIsAnalyzing(true);
    try {
      // In a real implementation, this would be an API call to the AI assistant
      // For now, we'll simulate a response after a delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Mock analysis data
      setAnalysisData({
        symbol,
        exchange,
        riskLevel: Math.random() > 0.5 ? 'high' : 'medium',
        recommendation: Math.random() > 0.5 ? 'reduce' : 'hold',
        analysis: `The position in ${symbol} on ${exchange} currently shows a ${Math.random() > 0.5 ? 'positive' : 'negative'} trend. Based on current market conditions and volatility, it is recommended to ${Math.random() > 0.5 ? 'reduce exposure' : 'hold position'}.`,
        metrics: {
          sharpeRatio: (Math.random() * 2).toFixed(2),
          maxDrawdown: (Math.random() * 15).toFixed(2) + '%',
          volatility: (Math.random() * 10).toFixed(2) + '%'
        },
        forecast: {
          shortTerm: Math.random() > 0.5 ? 'bullish' : 'bearish',
          mediumTerm: Math.random() > 0.5 ? 'bullish' : 'bearish',
          longTerm: Math.random() > 0.5 ? 'bullish' : 'bearish'
        }
      });
    } catch (err) {
      console.error('Error analyzing position:', err);
      setError('Failed to analyze position');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const closeAnalysis = () => {
    setAnalysisData(null);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatPercent = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value / 100);
  };

  const getPositionsBySymbol = () => {
    if (!positionsBySymbol) return [];
    return Object.entries(positionsBySymbol).map(([symbol, data]) => ({
      symbol,
      totalValue: data.total_value,
      totalUnrealizedPnl: data.total_unrealized_pnl,
      exchanges: data.exchanges
    }));
  };

  const getPositionsByExchange = () => {
    const exchangePositions = {};
    
    positions.forEach(position => {
      if (!exchangePositions[position.exchange]) {
        exchangePositions[position.exchange] = {
          exchange: position.exchange,
          positions: [],
          totalValue: 0,
          totalUnrealizedPnl: 0
        };
      }
      
      exchangePositions[position.exchange].positions.push(position);
      exchangePositions[position.exchange].totalValue += position.position_value || 0;
      exchangePositions[position.exchange].totalUnrealizedPnl += position.unrealized_pnl || 0;
    });
    
    return Object.values(exchangePositions);
  };

  const getPnlClass = (pnl) => {
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getBadgeClass = (pnl) => {
    if (pnl > 0) return 'bg-green-100 text-green-800';
    if (pnl < 0) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Positions</h1>
        <div className="flex items-center space-x-2">
          <WebSocketStatus 
            status={positionsStatus} 
            channel={Channels.POSITIONS} 
            error={positionsError}
            onReconnect={connectPositionsWs}
          />
          <button
            onClick={fetchPositions}
            className="px-3 py-1 bg-primary-600 text-white rounded hover:bg-primary-700 text-sm"
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
          <p className="text-sm">{error}</p>
        </div>
      )}
      
      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('all')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'all'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            All Positions
          </button>
          <button
            onClick={() => setActiveTab('by-symbol')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'by-symbol'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            By Symbol
          </button>
          <button
            onClick={() => setActiveTab('by-exchange')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'by-exchange'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            By Exchange
          </button>
        </nav>
      </div>
      
      {/* Positions Content */}
      {loading ? (
        <div className="text-center py-10">
          <svg className="animate-spin h-8 w-8 text-primary-500 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-2 text-gray-600">Loading positions...</p>
        </div>
      ) : (
        <>
          {/* All Positions View */}
          {activeTab === 'all' && (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {positions.length === 0 ? (
                  <li className="px-6 py-4 text-center text-gray-500">No positions found</li>
                ) : (
                  positions.map((position, index) => (
                    <li key={`${position.exchange}-${position.symbol}-${index}`} className="px-6 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="flex-shrink-0">
                            <div className={`h-10 w-10 rounded-full flex items-center justify-center ${position.side === 'long' ? 'bg-green-100' : 'bg-red-100'}`}>
                              {position.side === 'long' ? (
                                <ArrowTrendingUpIcon className="h-6 w-6 text-green-600" />
                              ) : (
                                <ArrowTrendingDownIcon className="h-6 w-6 text-red-600" />
                              )}
                            </div>
                          </div>
                          <div>
                            <h3 className="text-lg font-medium text-gray-900">{position.symbol}</h3>
                            <p className="text-sm text-gray-500">{position.exchange}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">Position Value</p>
                            <p className="text-sm text-gray-500">{formatCurrency(position.position_value || 0)}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">Unrealized PnL</p>
                            <p className={`text-sm ${getPnlClass(position.unrealized_pnl)}`}>
                              {formatCurrency(position.unrealized_pnl || 0)}
                            </p>
                          </div>
                          <button
                            onClick={() => analyzePosition(position.symbol, position.exchange)}
                            className="px-3 py-1 bg-secondary-600 text-white rounded hover:bg-secondary-700 text-sm"
                            disabled={isAnalyzing}
                          >
                            {isAnalyzing && selectedSymbol === position.symbol && selectedExchange === position.exchange
                              ? 'Analyzing...'
                              : 'Analyze'}
                          </button>
                        </div>
                      </div>
                      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-4">
                        <div>
                          <p className="text-xs text-gray-500">Side</p>
                          <p className="text-sm font-medium text-gray-900 capitalize">{position.side}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Size</p>
                          <p className="text-sm font-medium text-gray-900">{position.size || position.position_amt}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Entry Price</p>
                          <p className="text-sm font-medium text-gray-900">{formatCurrency(position.entry_price)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Current Price</p>
                          <p className="text-sm font-medium text-gray-900">{formatCurrency(position.current_price || position.mark_price)}</p>
                        </div>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </div>
          )}
          
          {/* By Symbol View */}
          {activeTab === 'by-symbol' && (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {getPositionsBySymbol().length === 0 ? (
                  <li className="px-6 py-4 text-center text-gray-500">No positions found</li>
                ) : (
                  getPositionsBySymbol().map((symbolData) => (
                    <li key={symbolData.symbol} className="px-6 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">{symbolData.symbol}</h3>
                          <p className="text-sm text-gray-500">
                            Exchanges: {Object.keys(symbolData.exchanges).join(', ')}
                          </p>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">Total Value</p>
                            <p className="text-sm text-gray-500">{formatCurrency(symbolData.totalValue)}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">Total Unrealized PnL</p>
                            <p className={`text-sm ${getPnlClass(symbolData.totalUnrealizedPnl)}`}>
                              {formatCurrency(symbolData.totalUnrealizedPnl)}
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="mt-4">
                        <h4 className="text-sm font-medium text-gray-500">Positions by Exchange</h4>
                        <div className="mt-2 divide-y divide-gray-200">
                          {Object.entries(symbolData.exchanges).map(([exchange, position]) => (
                            <div key={exchange} className="py-2 flex justify-between items-center">
                              <div>
                                <p className="text-sm font-medium text-gray-900 capitalize">{exchange}</p>
                                <div className="flex items-center space-x-2 text-xs text-gray-500">
                                  <span>Side: {position.side}</span>
                                  <span>•</span>
                                  <span>Size: {position.size || position.position_amt}</span>
                                </div>
                              </div>
                              <div className="flex items-center space-x-4">
                                <div className="text-right">
                                  <p className="text-xs text-gray-500">Entry / Current</p>
                                  <p className="text-sm text-gray-900">
                                    {formatCurrency(position.entry_price)} / {formatCurrency(position.current_price || position.mark_price)}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="text-xs text-gray-500">Unrealized PnL</p>
                                  <p className={`text-sm ${getPnlClass(position.unrealized_pnl)}`}>
                                    {formatCurrency(position.unrealized_pnl)}
                                  </p>
                                </div>
                                <button
                                  onClick={() => analyzePosition(symbolData.symbol, exchange)}
                                  className="px-3 py-1 bg-secondary-600 text-white rounded hover:bg-secondary-700 text-xs"
                                  disabled={isAnalyzing}
                                >
                                  {isAnalyzing && selectedSymbol === symbolData.symbol && selectedExchange === exchange
                                    ? 'Analyzing...'
                                    : 'Analyze'}
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </div>
          )}
          
          {/* By Exchange View */}
          {activeTab === 'by-exchange' && (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {getPositionsByExchange().length === 0 ? (
                  <li className="px-6 py-4 text-center text-gray-500">No positions found</li>
                ) : (
                  getPositionsByExchange().map((exchangeData) => (
                    <li key={exchangeData.exchange} className="px-6 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900 capitalize">{exchangeData.exchange}</h3>
                          <p className="text-sm text-gray-500">
                            {exchangeData.positions.length} position(s)
                          </p>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">Total Value</p>
                            <p className="text-sm text-gray-500">{formatCurrency(exchangeData.totalValue)}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">Total Unrealized PnL</p>
                            <p className={`text-sm ${getPnlClass(exchangeData.totalUnrealizedPnl)}`}>
                              {formatCurrency(exchangeData.totalUnrealizedPnl)}
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="mt-4 overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entry Price</th>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unrealized PnL</th>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {exchangeData.positions.map((position, index) => (
                              <tr key={`${position.symbol}-${index}`}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{position.symbol}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">{position.side}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{position.size || position.position_amt}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatCurrency(position.entry_price)}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatCurrency(position.current_price || position.mark_price)}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getBadgeClass(position.unrealized_pnl)}`}>
                                    {formatCurrency(position.unrealized_pnl)}
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                  <button
                                    onClick={() => analyzePosition(position.symbol, exchangeData.exchange)}
                                    className="px-3 py-1 bg-secondary-600 text-white rounded hover:bg-secondary-700 text-xs"
                                    disabled={isAnalyzing}
                                  >
                                    {isAnalyzing && selectedSymbol === position.symbol && selectedExchange === exchangeData.exchange
                                      ? 'Analyzing...'
                                      : 'Analyze'}
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </div>
          )}
        </>
      )}
      
      {/* Position Analysis Modal */}
      {analysisData && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">
                Analysis: {analysisData.symbol} ({analysisData.exchange})
              </h3>
              <button
                onClick={closeAnalysis}
                className="text-gray-400 hover:text-gray-500"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6">
              <div className="mb-6">
                <div className="flex items-center mb-2">
                  <span className="text-sm font-medium text-gray-900 mr-2">Risk Level:</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${analysisData.riskLevel === 'high' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                    {analysisData.riskLevel.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="text-sm font-medium text-gray-900 mr-2">Recommendation:</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${analysisData.recommendation === 'reduce' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                    {analysisData.recommendation.toUpperCase()}
                  </span>
                </div>
              </div>
              
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Analysis</h4>
                <p className="text-sm text-gray-600">{analysisData.analysis}</p>
              </div>
              
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Metrics</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-500">Sharpe Ratio</p>
                    <p className="text-sm font-medium">{analysisData.metrics.sharpeRatio}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-500">Max Drawdown</p>
                    <p className="text-sm font-medium">{analysisData.metrics.maxDrawdown}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-500">Volatility</p>
                    <p className="text-sm font-medium">{analysisData.metrics.volatility}</p>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Forecast</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-500">Short Term (24h)</p>
                    <p className={`text-sm font-medium ${analysisData.forecast.shortTerm === 'bullish' ? 'text-green-600' : 'text-red-600'}`}>
                      {analysisData.forecast.shortTerm.toUpperCase()}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-500">Medium Term (1w)</p>
                    <p className={`text-sm font-medium ${analysisData.forecast.mediumTerm === 'bullish' ? 'text-green-600' : 'text-red-600'}`}>
                      {analysisData.forecast.mediumTerm.toUpperCase()}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-500">Long Term (1m)</p>
                    <p className={`text-sm font-medium ${analysisData.forecast.longTerm === 'bullish' ? 'text-green-600' : 'text-red-600'}`}>
                      {analysisData.forecast.longTerm.toUpperCase()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="px-6 py-3 bg-gray-50 text-right">
              <button
                onClick={closeAnalysis}
                className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 