import { useState, useEffect } from 'react';
import axios from 'axios';
import useWebSocket from '../hooks/useWebSocket';
import { Channels } from '../services/websocket';

// Mock data for initial rendering
const mockData = {
  accountSummary: {
    total_equity: 125000,
    total_available_balance: 75000,
    unrealized_pnl: 5000,
    exchanges: {
      binance: {
        total_equity: 75000,
        available_balance: 50000,
        unrealized_pnl: 3000
      },
      hyperliquid: {
        total_equity: 50000,
        available_balance: 25000,
        unrealized_pnl: 2000
      }
    }
  },
  positionSummary: {
    total_position_value: 50000,
    total_unrealized_pnl: 5000,
    positions_by_symbol: {
      "BTCUSDT": {
        total_value: 30000,
        total_unrealized_pnl: 3000,
        exchanges: {
          binance: {
            symbol: "BTCUSDT",
            side: "long",
            entry_price: 40000,
            mark_price: 42000,
            position_amt: 0.75,
            unrealized_pnl: 1500
          }
        }
      },
      "ETHUSDT": {
        total_value: 20000,
        total_unrealized_pnl: 2000,
        exchanges: {
          hyperliquid: {
            symbol: "ETHUSDT",
            side: "long",
            entry_price: 2500,
            mark_price: 2600,
            position_amt: 8,
            unrealized_pnl: 800
          }
        }
      }
    }
  }
};

export default function Dashboard() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [accountSummary, setAccountSummary] = useState(mockData.accountSummary);
  const [positionSummary, setPositionSummary] = useState(mockData.positionSummary);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // WebSocket connections
  const { 
    data: positionsData, 
    status: positionsStatus, 
    isConnected: isPositionsConnected 
  } = useWebSocket(Channels.POSITIONS);
  
  const { 
    data: accountsData, 
    status: accountsStatus, 
    isConnected: isAccountsConnected 
  } = useWebSocket(Channels.ACCOUNTS);
  
  // Update position data when received from WebSocket
  useEffect(() => {
    if (positionsData) {
      setPositionSummary(positionsData);
      setLoading(false);
    }
  }, [positionsData]);
  
  // Update account data when received from WebSocket
  useEffect(() => {
    if (accountsData && accountsData.accounts) {
      // Transform the accounts data to match the expected format
      const transformedData = {
        total_equity: 0,
        total_available_balance: 0,
        unrealized_pnl: 0,
        exchanges: { ...accountsData.accounts }
      };
      
      // Calculate totals
      Object.values(accountsData.accounts).forEach(account => {
        transformedData.total_equity += account.equity || 0;
        transformedData.total_available_balance += account.available || 0;
        transformedData.unrealized_pnl += account.unrealized_pnl || 0;
      });
      
      setAccountSummary(transformedData);
      setLoading(false);
    }
  }, [accountsData]);

  // Check monitoring status on component mount
  useEffect(() => {
    checkMonitorStatus();
  }, []);

  const checkMonitorStatus = async () => {
    try {
      const response = await axios.get('/api/v1/accounts/monitor/status');
      if (response.data.status === 'success' && response.data.data) {
        setIsMonitoring(response.data.data.is_monitoring);
      }
    } catch (err) {
      console.error('Error checking monitoring status:', err);
      setError('Failed to check monitoring status');
    }
  };

  const startMonitoring = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/v1/accounts/monitor/start');
      if (response.data.status === 'success') {
        setIsMonitoring(true);
        await fetchData();
      }
    } catch (err) {
      console.error('Error starting monitoring:', err);
      setError('Failed to start monitoring');
    } finally {
      setLoading(false);
    }
  };

  const stopMonitoring = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/v1/accounts/monitor/stop');
      if (response.data.status === 'success') {
        setIsMonitoring(false);
      }
    } catch (err) {
      console.error('Error stopping monitoring:', err);
      setError('Failed to stop monitoring');
    } finally {
      setLoading(false);
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Only fetch data if WebSockets are not connected
      if (!isPositionsConnected) {
        const positionsResponse = await axios.get('/api/v1/positions');
        if (positionsResponse.data.status === 'success') {
          setPositionSummary(positionsResponse.data.data);
        }
      }
      
      if (!isAccountsConnected) {
        const accountsResponse = await axios.get('/api/v1/accounts');
        if (accountsResponse.data.status === 'success') {
          setAccountSummary(accountsResponse.data.data);
        }
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const getPnlBadgeClass = (pnl) => {
    if (pnl > 0) return 'bg-green-100 text-green-800';
    if (pnl < 0) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Monitoring Status */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Monitoring Status</h2>
            <p className="mt-1 text-sm text-gray-500">
              {isMonitoring ? 'Actively monitoring accounts and positions' : 'Monitoring is inactive'}
            </p>
          </div>
          <div>
            {isMonitoring ? (
              <button
                onClick={stopMonitoring}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                disabled={loading}
              >
                {loading ? 'Stopping...' : 'Stop Monitoring'}
              </button>
            ) : (
              <button
                onClick={startMonitoring}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                disabled={loading}
              >
                {loading ? 'Starting...' : 'Start Monitoring'}
              </button>
            )}
          </div>
        </div>
        
        {/* WebSocket Status */}
        <div className="mt-4 flex space-x-2">
          <div className={`px-2 py-1 rounded-md text-xs font-medium ${isPositionsConnected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
            Positions: {isPositionsConnected ? 'Live' : 'Offline'}
          </div>
          <div className={`px-2 py-1 rounded-md text-xs font-medium ${isAccountsConnected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
            Accounts: {isAccountsConnected ? 'Live' : 'Offline'}
          </div>
        </div>
      </div>

      {/* Account Summary */}
      <div className="bg-white shadow rounded-lg p-4">
        <h2 className="text-lg font-medium text-gray-900">Account Summary</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="bg-gray-50 rounded-md p-4">
            <h3 className="text-sm font-medium text-gray-500">Total Equity</h3>
            <p className="mt-1 text-2xl font-semibold text-gray-900">{formatCurrency(accountSummary.total_equity)}</p>
          </div>
          <div className="bg-gray-50 rounded-md p-4">
            <h3 className="text-sm font-medium text-gray-500">Available Balance</h3>
            <p className="mt-1 text-2xl font-semibold text-gray-900">{formatCurrency(accountSummary.total_available_balance)}</p>
          </div>
          <div className="bg-gray-50 rounded-md p-4">
            <h3 className="text-sm font-medium text-gray-500">Unrealized PnL</h3>
            <p className={`mt-1 text-2xl font-semibold ${accountSummary.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(accountSummary.unrealized_pnl)}
            </p>
          </div>
        </div>
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-500">By Exchange</h3>
          <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {Object.entries(accountSummary.exchanges).map(([exchange, data]) => (
              <div key={exchange} className="border rounded-md p-4">
                <h4 className="text-sm font-medium text-gray-900">{exchange.charAt(0).toUpperCase() + exchange.slice(1)}</h4>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <div>
                    <p className="text-xs text-gray-500">Equity</p>
                    <p className="text-sm font-medium">{formatCurrency(data.equity || data.total_equity || 0)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Available</p>
                    <p className="text-sm font-medium">{formatCurrency(data.available || data.available_balance || 0)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Unrealized PnL</p>
                    <p className={`text-sm font-medium ${(data.unrealized_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(data.unrealized_pnl || 0)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Position Summary */}
      <div className="bg-white shadow rounded-lg p-4">
        <h2 className="text-lg font-medium text-gray-900">Position Summary</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="bg-gray-50 rounded-md p-4">
            <h3 className="text-sm font-medium text-gray-500">Total Position Value</h3>
            <p className="mt-1 text-2xl font-semibold text-gray-900">{formatCurrency(positionSummary.total_position_value)}</p>
          </div>
          <div className="bg-gray-50 rounded-md p-4">
            <h3 className="text-sm font-medium text-gray-500">Total Unrealized PnL</h3>
            <p className={`mt-1 text-2xl font-semibold ${positionSummary.total_unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(positionSummary.total_unrealized_pnl)}
            </p>
          </div>
        </div>
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-500">By Symbol</h3>
          <div className="mt-2 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unrealized PnL</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Exchanges</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(positionSummary.positions_by_symbol).map(([symbol, data]) => (
                  <tr key={symbol}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{symbol}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatCurrency(data.total_value)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getPnlBadgeClass(data.total_unrealized_pnl)}`}>
                        {formatCurrency(data.total_unrealized_pnl)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {Object.keys(data.exchanges).join(', ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
} 