import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  ChartBarIcon, 
  BanknotesIcon, 
  ShieldExclamationIcon, 
  Cog6ToothIcon,
  ChatBubbleBottomCenterTextIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';
import AlertsContainer from './AlertsContainer';
import WebSocketStatus from './WebSocketStatus';
import useWebSocket from '../hooks/useWebSocket';
import { Channels } from '../services/websocket';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Positions', href: '/positions', icon: ChartBarIcon },
  { name: 'Accounts', href: '/accounts', icon: BanknotesIcon },
  { name: 'Risk Management', href: '/risk', icon: ShieldExclamationIcon },
  { name: 'Backtesting', href: '/backtesting', icon: BeakerIcon },
  { name: 'Configuration', href: '/config', icon: Cog6ToothIcon },
  { name: 'AI Assistant', href: '/assistant', icon: ChatBubbleBottomCenterTextIcon },
];

export default function Layout() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showWebSocketStatus, setShowWebSocketStatus] = useState(false);
  
  // Initialize WebSocket connections
  const positionsWs = useWebSocket(Channels.POSITIONS);
  const accountsWs = useWebSocket(Channels.ACCOUNTS);
  const riskMetricsWs = useWebSocket(Channels.RISK_METRICS);
  const alertsWs = useWebSocket(Channels.ALERTS);

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <div className={`bg-secondary-800 text-white w-64 flex-shrink-0 transition-all duration-300 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-64 md:translate-x-0'}`}>
        <div className="px-4 py-6">
          <h1 className="text-2xl font-bold">ETRMS</h1>
          <p className="text-sm text-secondary-400">Trading Risk Management</p>
        </div>
        <nav className="mt-5 px-2">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`
                flex items-center px-4 py-3 my-1 text-sm rounded-md
                ${location.pathname === item.href
                  ? 'bg-secondary-700 text-white'
                  : 'text-secondary-300 hover:bg-secondary-700 hover:text-white'}
              `}
            >
              <item.icon className="h-5 w-5 mr-3" />
              {item.name}
            </Link>
          ))}
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white shadow-sm z-10">
          <div className="px-4 py-4 flex justify-between items-center">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden text-secondary-500 hover:text-secondary-700"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="text-xl font-semibold text-secondary-900">
              {navigation.find(item => item.href === location.pathname)?.name || 'Dashboard'}
            </div>
            <div className="flex items-center space-x-4">
              <button 
                className="text-secondary-500 hover:text-secondary-700 relative"
                onClick={() => setShowWebSocketStatus(!showWebSocketStatus)}
                title="WebSocket Status"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                {(positionsWs.hasError || accountsWs.hasError || riskMetricsWs.hasError || alertsWs.hasError) && (
                  <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-400 ring-2 ring-white"></span>
                )}
              </button>
              <button className="text-secondary-500 hover:text-secondary-700">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </button>
              <div className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center text-white font-bold">
                U
              </div>
            </div>
          </div>
          
          {/* WebSocket Status Panel */}
          {showWebSocketStatus && (
            <div className="bg-white border-t border-gray-200 p-4 space-y-2">
              <h3 className="text-sm font-medium text-gray-700">WebSocket Connections</h3>
              <div className="flex flex-wrap gap-2">
                <WebSocketStatus 
                  status={positionsWs.status} 
                  channel={Channels.POSITIONS} 
                  error={positionsWs.error}
                  onReconnect={positionsWs.connect}
                />
                <WebSocketStatus 
                  status={accountsWs.status} 
                  channel={Channels.ACCOUNTS} 
                  error={accountsWs.error}
                  onReconnect={accountsWs.connect}
                />
                <WebSocketStatus 
                  status={riskMetricsWs.status} 
                  channel={Channels.RISK_METRICS} 
                  error={riskMetricsWs.error}
                  onReconnect={riskMetricsWs.connect}
                />
                <WebSocketStatus 
                  status={alertsWs.status} 
                  channel={Channels.ALERTS} 
                  error={alertsWs.error}
                  onReconnect={alertsWs.connect}
                />
              </div>
            </div>
          )}
        </header>
        <main className="flex-1 overflow-auto p-6 bg-secondary-50">
          <Outlet />
        </main>
        
        {/* Alerts Container */}
        <AlertsContainer />
      </div>
    </div>
  );
} 