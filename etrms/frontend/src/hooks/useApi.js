import { useState, useCallback } from 'react';

/**
 * Custom hook for making API calls to the backend
 * Provides methods for GET, POST, PUT, and DELETE requests
 * Handles error handling and response parsing
 */
export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Make a GET request to the specified endpoint
   * @param {string} endpoint - The API endpoint to call
   * @param {Object} params - Optional query parameters
   * @returns {Promise<Object>} - The response data
   */
  const get = useCallback(async (endpoint, params = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      // Build query string from params
      const queryString = Object.keys(params).length > 0
        ? `?${new URLSearchParams(params).toString()}`
        : '';
      
      // In a real implementation, this would be the actual API URL
      // For now, we'll simulate responses for development
      if (endpoint.includes('/exchanges') && !endpoint.includes('/symbols')) {
        // Simulate a delay
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Return mock exchanges
        return {
          status: 'success',
          data: ['binance', 'hyperliquid', 'bybit']
        };
      }
      
      if (endpoint.includes('/symbols')) {
        // Simulate a delay
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Extract exchange from endpoint
        const exchange = endpoint.split('/')[3];
        
        // Return mock symbols based on exchange
        if (exchange === 'binance') {
          return {
            status: 'success',
            data: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT']
          };
        } else if (exchange === 'hyperliquid') {
          return {
            status: 'success',
            data: ['BTCUSD', 'ETHUSD', 'SOLUSD', 'BNBUSD', 'ADAUSD']
          };
        } else if (exchange === 'bybit') {
          return {
            status: 'success',
            data: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT']
          };
        }
      }
      
      // For other endpoints, make the actual API call
      const response = await fetch(`${endpoint}${queryString}`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      return data;
    } catch (err) {
      console.error('API GET error:', err);
      setError(err.message || 'An error occurred while fetching data');
      return {
        status: 'error',
        error: err.message || 'An error occurred while fetching data'
      };
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Make a POST request to the specified endpoint
   * @param {string} endpoint - The API endpoint to call
   * @param {Object} data - The data to send in the request body
   * @returns {Promise<Object>} - The response data
   */
  const post = useCallback(async (endpoint, data = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      // In a real implementation, this would be the actual API call
      // For now, we'll simulate responses for development
      
      // Simulate a delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Simulate responses for specific endpoints
      if (endpoint.includes('/analysis/setups')) {
        return {
          status: 'success',
          data: [
            {
              id: 'setup_1',
              exchange: data.exchange || 'binance',
              symbol: data.symbol || 'BTCUSDT',
              setup_type: 'breakout',
              timeframe: data.timeframe || '1h',
              quality: 0.85,
              direction: 'long',
              detected_at: new Date().toISOString(),
              key_levels: {
                entry: 42000,
                stop_loss: 41200,
                targets: [43500, 45000]
              },
              indicators: {
                rsi: 68,
                volume_change: 1.45,
                support_level: 41200
              },
              description: 'Bullish breakout from ascending triangle pattern with increasing volume.'
            },
            {
              id: 'setup_2',
              exchange: data.exchange || 'binance',
              symbol: data.symbol || 'ETHUSDT',
              setup_type: 'trend_continuation',
              timeframe: data.timeframe || '1h',
              quality: 0.78,
              direction: 'long',
              detected_at: new Date().toISOString(),
              key_levels: {
                entry: 2850,
                stop_loss: 2780,
                targets: [2950, 3050]
              },
              indicators: {
                rsi: 62,
                volume_change: 1.2,
                support_level: 2780
              },
              description: 'Bullish trend continuation after pullback to 20 EMA with bullish engulfing pattern.'
            },
            {
              id: 'setup_3',
              exchange: data.exchange || 'binance',
              symbol: data.symbol || 'SOLUSDT',
              setup_type: 'trend_reversal',
              timeframe: data.timeframe || '1h',
              quality: 0.72,
              direction: 'short',
              detected_at: new Date().toISOString(),
              key_levels: {
                entry: 95,
                stop_loss: 98,
                targets: [90, 85]
              },
              indicators: {
                rsi: 72,
                volume_change: 1.1,
                resistance_level: 98
              },
              description: 'Bearish reversal at key resistance with divergence on RSI and decreasing volume.'
            }
          ]
        };
      }
      
      if (endpoint.includes('/analysis/recommendations')) {
        return {
          status: 'success',
          data: [
            {
              id: 'rec_1',
              setup_id: data.setup_id || 'setup_1',
              exchange: data.exchange || 'binance',
              symbol: data.symbol || 'BTCUSDT',
              strategy_type: 'breakout',
              timeframe: data.timeframe || '1h',
              direction: 'long',
              confidence: 0.82,
              entry: {
                price: 42000,
                type: 'limit',
                zone: [41900, 42100]
              },
              exit: {
                stop_loss: 41200,
                take_profit: [43500, 45000],
                trailing_stop: {
                  activation: 43000,
                  offset: 1.5
                }
              },
              position_sizing: {
                recommended_size: '2% of portfolio',
                max_size: '5% of portfolio',
                risk_reward: 3.2
              },
              timeframe_confirmation: {
                higher: true,
                same: true,
                lower: true
              },
              notes: 'Strong breakout with increasing volume. Consider scaling in if price retests breakout level.'
            },
            {
              id: 'rec_2',
              setup_id: data.setup_id || 'setup_2',
              exchange: data.exchange || 'binance',
              symbol: data.symbol || 'ETHUSDT',
              strategy_type: 'trend_following',
              timeframe: data.timeframe || '1h',
              direction: 'long',
              confidence: 0.75,
              entry: {
                price: 2850,
                type: 'limit',
                zone: [2830, 2870]
              },
              exit: {
                stop_loss: 2780,
                take_profit: [2950, 3050],
                trailing_stop: {
                  activation: 2920,
                  offset: 1.2
                }
              },
              position_sizing: {
                recommended_size: '1.5% of portfolio',
                max_size: '4% of portfolio',
                risk_reward: 2.8
              },
              timeframe_confirmation: {
                higher: true,
                same: true,
                lower: false
              },
              notes: 'Trend continuation setup with moderate volume. Watch for rejection at previous high around 2950.'
            }
          ]
        };
      }
      
      if (endpoint.includes('/analysis/risk-assessment')) {
        return {
          status: 'success',
          data: {
            setup_id: data.setup_id || 'setup_1',
            recommendation_id: data.recommendation_id || 'rec_1',
            overall_risk: 0.35,
            risk_factors: {
              market_regime: {
                score: 0.2,
                description: 'Current trending market regime is favorable for this setup type'
              },
              volatility: {
                score: 0.4,
                description: 'Moderate volatility may cause wider price swings than normal'
              },
              liquidity: {
                score: 0.3,
                description: 'Good liquidity for the chosen position size'
              },
              correlation: {
                score: 0.5,
                description: 'Moderate correlation with existing portfolio positions'
              },
              news_events: {
                score: 0.4,
                description: 'No major news events expected in the next 24 hours'
              }
            },
            portfolio_impact: {
              current_exposure: '15% in crypto assets',
              additional_exposure: '2%',
              max_drawdown_estimate: '0.8% of portfolio',
              correlation_with_portfolio: 0.65
            },
            warnings: [
              'Moderate correlation with existing positions may amplify drawdowns',
              'Consider reducing position size if volatility increases'
            ],
            recommendations: [
              'Proceed with recommended position size',
              'Use a limit order to enter at the lower end of the entry zone',
              'Consider implementing a trailing stop after the first target is reached'
            ]
          }
        };
      }
      
      if (endpoint.includes('/analysis/checklist')) {
        return {
          status: 'success',
          data: {
            setup_id: data.setup_id || 'setup_1',
            recommendation_id: data.recommendation_id || 'rec_1',
            checklist_items: [
              {
                id: 'item_1',
                category: 'setup_validation',
                description: 'Setup matches my trading plan',
                importance: 'critical'
              },
              {
                id: 'item_2',
                category: 'setup_validation',
                description: 'Setup is confirmed on multiple timeframes',
                importance: 'high'
              },
              {
                id: 'item_3',
                category: 'risk_management',
                description: 'Position size is within my risk limits',
                importance: 'critical'
              },
              {
                id: 'item_4',
                category: 'risk_management',
                description: 'Stop loss is placed at a logical level',
                importance: 'critical'
              },
              {
                id: 'item_5',
                category: 'market_conditions',
                description: 'Current market regime is favorable for this setup',
                importance: 'high'
              },
              {
                id: 'item_6',
                category: 'market_conditions',
                description: 'No major news events expected during the trade',
                importance: 'medium'
              },
              {
                id: 'item_7',
                category: 'execution',
                description: 'Entry order type is appropriate for current liquidity',
                importance: 'medium'
              },
              {
                id: 'item_8',
                category: 'execution',
                description: 'Take profit levels are set at logical resistance/support',
                importance: 'high'
              },
              {
                id: 'item_9',
                category: 'psychological',
                description: 'I am trading with a clear mind, not emotional',
                importance: 'high'
              },
              {
                id: 'item_10',
                category: 'psychological',
                description: 'I am not trying to recover previous losses',
                importance: 'high'
              }
            ]
          }
        };
      }
      
      if (endpoint.includes('/analysis/scenarios')) {
        return {
          status: 'success',
          data: {
            setup_id: data.setup_id || 'setup_1',
            recommendation_id: data.recommendation_id || 'rec_1',
            scenarios: [
              {
                id: 'scenario_1',
                type: 'best_case',
                probability: 0.3,
                description: 'Price breaks out strongly and reaches the second target',
                outcome: {
                  profit_loss: 7.1,
                  profit_loss_amount: 710,
                  time_to_completion: '2-3 days'
                },
                key_indicators: {
                  volume_increase: 'Strong volume confirmation',
                  momentum: 'RSI remains above 60',
                  support_resistance: 'No major resistance until target 2'
                }
              },
              {
                id: 'scenario_2',
                type: 'base_case',
                probability: 0.5,
                description: 'Price moves to the first target and consolidates',
                outcome: {
                  profit_loss: 3.6,
                  profit_loss_amount: 360,
                  time_to_completion: '1-2 days'
                },
                key_indicators: {
                  volume_increase: 'Moderate volume',
                  momentum: 'RSI between 50-60',
                  support_resistance: 'Resistance at first target'
                }
              },
              {
                id: 'scenario_3',
                type: 'worst_case',
                probability: 0.2,
                description: 'Price rejects at entry and hits stop loss',
                outcome: {
                  profit_loss: -1.9,
                  profit_loss_amount: -190,
                  time_to_completion: '12-24 hours'
                },
                key_indicators: {
                  volume_increase: 'Low volume or selling pressure',
                  momentum: 'RSI drops below 45',
                  support_resistance: 'Support breaks at stop loss level'
                }
              }
            ]
          }
        };
      }
      
      // For other endpoints, make the actual API call
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const responseData = await response.json();
      return responseData;
    } catch (err) {
      console.error('API POST error:', err);
      setError(err.message || 'An error occurred while sending data');
      return {
        status: 'error',
        error: err.message || 'An error occurred while sending data'
      };
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Make a PUT request to the specified endpoint
   * @param {string} endpoint - The API endpoint to call
   * @param {Object} data - The data to send in the request body
   * @returns {Promise<Object>} - The response data
   */
  const put = useCallback(async (endpoint, data = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(endpoint, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const responseData = await response.json();
      return responseData;
    } catch (err) {
      console.error('API PUT error:', err);
      setError(err.message || 'An error occurred while updating data');
      return {
        status: 'error',
        error: err.message || 'An error occurred while updating data'
      };
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Make a DELETE request to the specified endpoint
   * @param {string} endpoint - The API endpoint to call
   * @returns {Promise<Object>} - The response data
   */
  const del = useCallback(async (endpoint) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(endpoint, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const responseData = await response.json();
      return responseData;
    } catch (err) {
      console.error('API DELETE error:', err);
      setError(err.message || 'An error occurred while deleting data');
      return {
        status: 'error',
        error: err.message || 'An error occurred while deleting data'
      };
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    get,
    post,
    put,
    del,
    loading,
    error
  };
};

export default useApi; 