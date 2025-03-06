import { useState, useEffect } from 'react';
import axios from 'axios';
import useWebSocket from '../hooks/useWebSocket';
import { Channels } from '../services/websocket';
import WebSocketStatus from '../components/WebSocketStatus';
import { CurrencyDollarIcon, BanknotesIcon, ArrowsRightLeftIcon, ClockIcon } from '@heroicons/react/24/outline';

export default function Accounts() {
  const [accounts, setAccounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary', 'binance', 'hyperliquid'
  const [selectedExchange, setSelectedExchange] = useState(null);
  const [monitorStatus, setMonitorStatus] = useState({ is_monitoring: false });
  
  // WebSocket connection for real-time account data
  const { 
    data: accountsData, 
    status: accountsStatus, 
    isConnected: isAccountsConnected,
    connect: connectAccountsWs,
    error: accountsError
  } = useWebSocket(Channels.ACCOUNTS);

  // Mock data for initial rendering
  const mockAccounts = {
    "total_equity": 125000,
    "total_available_balance": 75000,
    "unrealized_pnl": 5000,
    "exchanges": {
      "binance": {
        "total_equity": 75000,
        "available_balance": 50000,
        "unrealized_pnl": 3000,
        "margin_balance": 25000,
        "wallet_balance": 72000,
        "positions_count": 1,
        "max_withdrawal": 48000,
        "used_margin": 25000,
        "update_time": new Date().getTime() - 30000, // 30 seconds ago
        "history": [
          { date: "2023-09-15", balance: 70000 },
          { date: "2023-09-16", balance: 68000 },
          { date: "2023-09-17", balance: 71000 },
          { date: "2023-09-18", balance: 74000 },
          { date: "2023-09-19", balance: 75000 }
        ]
      },
      "hyperliquid": {
        "total_equity": 50000,
        "available_balance": 25000,
        "unrealized_pnl": 2000,
        "margin_balance": 27000,
        "wallet_balance": 48000,
        "positions_count": 1,
        "max_withdrawal": 23000,
        "used_margin": 23000,
        "update_time": new Date().getTime() - 45000, // 45 seconds ago
        "history": [
          { date: "2023-09-15", balance: 45000 },
          { date: "2023-09-16", balance: 46000 },
          { date: "2023-09-17", balance: 47500 },
          { date: "2023-09-18", balance: 48500 },
          { date: "2023-09-19", balance: 50000 }
        ]
      }
    }
  };

  // Update accounts when received from WebSocket
  useEffect(() => {
    if (accountsData) {
      // Update accounts state from WebSocket data
      if (accountsData.data && accountsData.data.exchanges) {
        // Format from API response
        setAccounts(accountsData.data);
      } else if (accountsData.exchanges) {
        // Format from direct WebSocket
        setAccounts(accountsData);
      }
      
      // If monitoring status is included, update it
      if (accountsData.monitoring_status || (accountsData.data && accountsData.data.monitoring_status)) {
        setMonitorStatus(accountsData.monitoring_status || accountsData.data.monitoring_status);
      }
      
      setLoading(false);
    }
  }, [accountsData]);

  // Fetch accounts data initially or when WebSocket is not connected
  useEffect(() => {
    if (!isAccountsConnected) {
      fetchAccounts();
    }
  }, [isAccountsConnected]);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/accounts');
      if (response.data.status === 'success' && response.data.data) {
        setAccounts(response.data.data);
        
        // If monitoring status is included, update it
        if (response.data.data.monitoring_status) {
          setMonitorStatus(response.data.data.monitoring_status);
        } else {
          // Fetch monitoring status separately
          const statusResponse = await axios.get('/api/v1/accounts/monitor/status');
          if (statusResponse.data.status === 'success') {
            setMonitorStatus(statusResponse.data.data);
          }
        }
      } else {
        // Use mock data for development
        setAccounts(mockAccounts);
      }
      setLoading(false);
    } catch (err) {
      console.error('Error fetching accounts:', err);
      setError('Failed to fetch account data. Please try again.');
      
      // Use mock data for development
      setAccounts(mockAccounts);
      setLoading(false);
    }
  };

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  // Get badge color based on PnL
  const getPnlBadgeClass = (pnl) => {
    if (pnl > 0) return 'badge-success';
    if (pnl < 0) return 'badge-danger';
    return 'badge-warning';
  };

  // Format timestamp to readable time
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // Calculate time since update
  const getTimeSinceUpdate = (timestamp) => {
    const now = Date.now();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) {
      return `${seconds} seconds ago`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)} minutes ago`;
    } else {
      return `${Math.floor(seconds / 3600)} hours ago`;
    }
  };

  // Handle starting monitoring
  const handleStartMonitoring = async () => {
    try {
      const response = await axios.post('/api/v1/accounts/monitor/start');
      if (response.data.status === 'success') {
        // Get updated status
        const statusResponse = await axios.get('/api/v1/accounts/monitor/status');
        if (statusResponse.data.status === 'success') {
          setMonitorStatus(statusResponse.data.data);
        } else {
          // Fallback to assuming monitoring is on
          setMonitorStatus({ is_monitoring: true });
        }
      } else {
        setError('Failed to start monitoring: ' + (response.data.message || 'Unknown error'));
      }
    } catch (err) {
      console.error('Error starting monitoring:', err);
      setError('Failed to start monitoring. Please try again.');
      
      // For development without API
      setMonitorStatus({ is_monitoring: true });
    }
  };

  // Handle stopping monitoring
  const handleStopMonitoring = async () => {
    try {
      const response = await axios.post('/api/v1/accounts/monitor/stop');
      if (response.data.status === 'success') {
        // Get updated status
        const statusResponse = await axios.get('/api/v1/accounts/monitor/status');
        if (statusResponse.data.status === 'success') {
          setMonitorStatus(statusResponse.data.data);
        } else {
          // Fallback to assuming monitoring is off
          setMonitorStatus({ is_monitoring: false });
        }
      } else {
        setError('Failed to stop monitoring: ' + (response.data.message || 'Unknown error'));
      }
    } catch (err) {
      console.error('Error stopping monitoring:', err);
      setError('Failed to stop monitoring. Please try again.');
      
      // For development without API
      setMonitorStatus({ is_monitoring: false });
    }
  };

  // Render the summary tab
  const renderSummary = () => {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card bg-white shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-secondary-500 text-sm">Total Equity</p>
                <p className="text-2xl font-bold">{formatCurrency(accounts.total_equity)}</p>
              </div>
              <div className="p-2 bg-primary-100 rounded-lg">
                <CurrencyDollarIcon className="h-6 w-6 text-primary-500" />
              </div>
            </div>
          </div>
          <div className="card bg-white shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-secondary-500 text-sm">Available Balance</p>
                <p className="text-2xl font-bold">{formatCurrency(accounts.total_available_balance)}</p>
              </div>
              <div className="p-2 bg-success-100 rounded-lg">
                <BanknotesIcon className="h-6 w-6 text-success-500" />
              </div>
            </div>
          </div>
          <div className="card bg-white shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-secondary-500 text-sm">Unrealized P&L</p>
                <div className="flex items-center">
                  <p className="text-2xl font-bold mr-2">{formatCurrency(accounts.unrealized_pnl)}</p>
                  <span className={`badge ${getPnlBadgeClass(accounts.unrealized_pnl)}`}>
                    {accounts.unrealized_pnl >= 0 ? '+' : ''}
                    {(accounts.unrealized_pnl / accounts.total_equity * 100).toFixed(2)}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-secondary-100 rounded-lg">
                <ArrowsRightLeftIcon className="h-6 w-6 text-secondary-500" />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Exchange Accounts</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white">
              <thead>
                <tr className="bg-secondary-100 text-secondary-600 text-left">
                  <th className="px-4 py-2">Exchange</th>
                  <th className="px-4 py-2">Total Equity</th>
                  <th className="px-4 py-2">Available Balance</th>
                  <th className="px-4 py-2">Unrealized P&L</th>
                  <th className="px-4 py-2">Positions</th>
                  <th className="px-4 py-2">Last Update</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(accounts.exchanges || {}).map(([exchange, data]) => (
                  <tr key={exchange} className="border-b">
                    <td className="px-4 py-2 capitalize">
                      <button
                        onClick={() => setActiveTab(exchange)}
                        className="text-primary-600 hover:text-primary-800 font-medium"
                      >
                        {exchange}
                      </button>
                    </td>
                    <td className="px-4 py-2">{formatCurrency(data.total_equity)}</td>
                    <td className="px-4 py-2">{formatCurrency(data.available_balance)}</td>
                    <td className="px-4 py-2">
                      <div className="flex items-center">
                        <span className="mr-2">{formatCurrency(data.unrealized_pnl)}</span>
                        <span className={`badge ${getPnlBadgeClass(data.unrealized_pnl)}`}>
                          {data.unrealized_pnl >= 0 ? '+' : ''}
                          {(data.unrealized_pnl / data.total_equity * 100).toFixed(2)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-2">{data.positions_count}</td>
                    <td className="px-4 py-2">
                      <div className="flex items-center text-secondary-500">
                        <ClockIcon className="h-4 w-4 mr-1" />
                        <span>{getTimeSinceUpdate(data.update_time)}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Render an exchange-specific tab
  const renderExchangeTab = (exchange) => {
    const data = accounts.exchanges?.[exchange];
    
    if (!data) {
      return (
        <div className="card">
          <p className="text-secondary-500">No data available for this exchange.</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card bg-white shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-secondary-500 text-sm">Total Equity</p>
                <p className="text-2xl font-bold">{formatCurrency(data.total_equity)}</p>
              </div>
              <div className="p-2 bg-primary-100 rounded-lg">
                <CurrencyDollarIcon className="h-6 w-6 text-primary-500" />
              </div>
            </div>
          </div>
          <div className="card bg-white shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-secondary-500 text-sm">Available Balance</p>
                <p className="text-2xl font-bold">{formatCurrency(data.available_balance)}</p>
              </div>
              <div className="p-2 bg-success-100 rounded-lg">
                <BanknotesIcon className="h-6 w-6 text-success-500" />
              </div>
            </div>
          </div>
          <div className="card bg-white shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-secondary-500 text-sm">Unrealized P&L</p>
                <div className="flex items-center">
                  <p className="text-2xl font-bold mr-2">{formatCurrency(data.unrealized_pnl)}</p>
                  <span className={`badge ${getPnlBadgeClass(data.unrealized_pnl)}`}>
                    {data.unrealized_pnl >= 0 ? '+' : ''}
                    {(data.unrealized_pnl / data.total_equity * 100).toFixed(2)}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-secondary-100 rounded-lg">
                <ArrowsRightLeftIcon className="h-6 w-6 text-secondary-500" />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Account Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="mb-4">
                <p className="text-secondary-500 text-sm">Wallet Balance</p>
                <p className="text-lg font-semibold">{formatCurrency(data.wallet_balance)}</p>
              </div>
              <div className="mb-4">
                <p className="text-secondary-500 text-sm">Margin Balance</p>
                <p className="text-lg font-semibold">{formatCurrency(data.margin_balance)}</p>
              </div>
            </div>
            <div>
              <div className="mb-4">
                <p className="text-secondary-500 text-sm">Used Margin</p>
                <p className="text-lg font-semibold">{formatCurrency(data.used_margin)}</p>
              </div>
              <div className="mb-4">
                <p className="text-secondary-500 text-sm">Max Withdrawal</p>
                <p className="text-lg font-semibold">{formatCurrency(data.max_withdrawal)}</p>
              </div>
            </div>
          </div>
          <div className="mt-4">
            <p className="text-secondary-500 text-sm">Last Update</p>
            <div className="flex items-center">
              <ClockIcon className="h-4 w-4 mr-1 text-secondary-500" />
              <span>{formatTime(data.update_time)} ({getTimeSinceUpdate(data.update_time)})</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Balance History</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white">
              <thead>
                <tr className="bg-secondary-100 text-secondary-600 text-left">
                  <th className="px-4 py-2">Date</th>
                  <th className="px-4 py-2">Balance</th>
                </tr>
              </thead>
              <tbody>
                {data.history.map((entry, index) => (
                  <tr key={index} className="border-b">
                    <td className="px-4 py-2">{entry.date}</td>
                    <td className="px-4 py-2">{formatCurrency(entry.balance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Accounts</h1>
        <div className="flex items-center space-x-4">
          {/* WebSocket Status Indicator */}
          <WebSocketStatus 
            status={accountsStatus} 
            channel="Accounts" 
            error={accountsError}
            onReconnect={connectAccountsWs}
          />
        
          {monitorStatus.is_monitoring ? (
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-success-600">
                <div className="h-2 w-2 rounded-full bg-success-500 mr-2 animate-pulse"></div>
                <span>Monitoring Active</span>
              </div>
              <button
                onClick={handleStopMonitoring}
                className="btn btn-danger"
              >
                Stop Monitoring
              </button>
            </div>
          ) : (
            <button
              onClick={handleStartMonitoring}
              className="btn btn-primary"
            >
              Start Monitoring
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-danger-100 border border-danger-400 text-danger-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
          <button
            className="absolute top-0 bottom-0 right-0 px-4 py-3"
            onClick={() => setError(null)}
          >
            <span className="text-danger-500">×</span>
          </button>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      ) : (
        <>
          {/* Tab Navigation */}
          <div className="border-b border-secondary-200">
            <nav className="-mb-px flex">
              <button
                onClick={() => setActiveTab('summary')}
                className={`py-2 px-4 border-b-2 font-medium text-sm ${
                  activeTab === 'summary'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                }`}
              >
                Summary
              </button>
              {Object.keys(accounts.exchanges || {}).map(exchange => (
                <button
                  key={exchange}
                  onClick={() => setActiveTab(exchange)}
                  className={`py-2 px-4 border-b-2 font-medium text-sm capitalize ${
                    activeTab === exchange
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                  }`}
                >
                  {exchange}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="mt-6">
            {activeTab === 'summary' ? renderSummary() : renderExchangeTab(activeTab)}
          </div>
        </>
      )}
    </div>
  );
} 