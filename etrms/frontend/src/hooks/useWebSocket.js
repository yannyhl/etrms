/**
 * Custom hook for using WebSockets in React components
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './useAuth';

// WebSocket connection status
export const ConnectionStatus = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
};

// Available WebSocket channels
export const Channels = {
  RISK_METRICS: 'risk-metrics',
  POSITIONS: 'positions',
  ACCOUNT_INFO: 'account-info',
  CIRCUIT_BREAKER_EVENTS: 'circuit-breaker-events',
};

/**
 * Custom hook for WebSocket connections
 * 
 * @param {string} channel - The WebSocket channel to connect to
 * @param {Object} options - Additional options
 * @param {boolean} options.autoConnect - Whether to connect automatically (default: true)
 * @param {number} options.reconnectInterval - Interval in ms between reconnection attempts (default: 5000)
 * @param {number} options.maxReconnectAttempts - Maximum number of reconnection attempts (default: 5)
 * @returns {Object} WebSocket state and control functions
 */
export const useWebSocket = (channel, options = {}) => {
  const {
    autoConnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
  } = options;

  const { token } = useAuth();
  const [status, setStatus] = useState(ConnectionStatus.DISCONNECTED);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [reconnectCount, setReconnectCount] = useState(0);
  
  const ws = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Get the WebSocket URL for the specified channel
  const getWebSocketUrl = useCallback(() => {
    const baseUrl = process.env.REACT_APP_API_WS_URL || 
      (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + 
      '//' + 
      (process.env.REACT_APP_API_HOST || window.location.host) + 
      '/api/ws';
    
    return `${baseUrl}/${channel}?token=${token}`;
  }, [channel, token]);

  // Connect to the WebSocket
  const connect = useCallback(() => {
    if (!token) {
      setStatus(ConnectionStatus.ERROR);
      setError(new Error('Authentication token is required'));
      return;
    }

    // Close existing connection if any
    if (ws.current) {
      ws.current.close();
    }

    // Clear any pending reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      setStatus(ConnectionStatus.CONNECTING);
      const url = getWebSocketUrl();
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setStatus(ConnectionStatus.CONNECTED);
        setError(null);
        setReconnectCount(0);
      };

      ws.current.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          setData(parsedData);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setStatus(ConnectionStatus.ERROR);
        setError(new Error('WebSocket connection error'));
      };

      ws.current.onclose = (event) => {
        setStatus(ConnectionStatus.DISCONNECTED);
        
        // Attempt to reconnect if not closed cleanly and within max attempts
        if (!event.wasClean && reconnectCount < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectCount(prev => prev + 1);
            connect();
          }, reconnectInterval);
        }
      };
    } catch (err) {
      setStatus(ConnectionStatus.ERROR);
      setError(err);
    }
  }, [token, getWebSocketUrl, reconnectCount, maxReconnectAttempts, reconnectInterval]);

  // Disconnect from the WebSocket
  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setStatus(ConnectionStatus.DISCONNECTED);
  }, []);

  // Connect on mount if autoConnect is true
  useEffect(() => {
    if (autoConnect && token) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect, token, connect, disconnect]);

  // Send a message to the WebSocket
  const send = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(typeof message === 'string' ? message : JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  return {
    status,
    data,
    error,
    isConnected: status === ConnectionStatus.CONNECTED,
    isConnecting: status === ConnectionStatus.CONNECTING,
    isDisconnected: status === ConnectionStatus.DISCONNECTED,
    hasError: status === ConnectionStatus.ERROR,
    connect,
    disconnect,
    send,
    reconnectCount,
  };
};

// Add default export
export default useWebSocket; 