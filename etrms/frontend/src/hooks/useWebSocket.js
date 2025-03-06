/**
 * Custom hook for using WebSockets in React components
 */
import { useState, useEffect, useCallback } from 'react';
import websocketService, { ConnectionStatus, Channels } from '../services/websocket';

/**
 * Hook for connecting to a WebSocket channel
 * 
 * @param {string} channel - The channel to connect to (from Channels enum)
 * @param {boolean} autoConnect - Whether to connect automatically on mount
 * @returns {Object} - WebSocket state and control functions
 */
const useWebSocket = (channel, autoConnect = true) => {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState(ConnectionStatus.DISCONNECTED);
  const [error, setError] = useState(null);

  // Handle incoming messages
  const handleMessage = useCallback((message) => {
    setData(message);
  }, []);

  // Handle connection status changes
  const handleStatusChange = useCallback((newStatus, err) => {
    setStatus(newStatus);
    if (err) {
      setError(err);
    } else if (newStatus === ConnectionStatus.CONNECTED) {
      setError(null);
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (status === ConnectionStatus.CONNECTING) return;
    
    websocketService
      .connect(channel, handleMessage, handleStatusChange)
      .catch(err => {
        console.error(`Error connecting to ${channel} WebSocket:`, err);
        setError(err);
      });
  }, [channel, handleMessage, handleStatusChange, status]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    websocketService.disconnect(channel);
    setStatus(ConnectionStatus.DISCONNECTED);
  }, [channel]);

  // Connect on mount if autoConnect is true
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Disconnect on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    data,
    status,
    error,
    isConnected: status === ConnectionStatus.CONNECTED,
    isConnecting: status === ConnectionStatus.CONNECTING,
    isDisconnected: status === ConnectionStatus.DISCONNECTED,
    hasError: status === ConnectionStatus.ERROR,
    connect,
    disconnect
  };
};

export default useWebSocket; 