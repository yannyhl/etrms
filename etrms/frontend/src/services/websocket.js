/**
 * WebSocket Service for ETRMS
 * 
 * This service manages WebSocket connections to the backend for real-time updates
 * on positions, accounts, risk metrics, and alerts.
 */

// Base URL for WebSocket connections
const WS_BASE_URL = process.env.NODE_ENV === 'production' 
  ? `wss://${window.location.host}/api/v1/ws`
  : `ws://${window.location.hostname}:8000/api/v1/ws`;

// WebSocket connection status enum
export const ConnectionStatus = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error'
};

// Available WebSocket channels
export const Channels = {
  POSITIONS: 'positions',
  ACCOUNTS: 'accounts',
  RISK_METRICS: 'risk-metrics',
  ALERTS: 'alerts'
};

class WebSocketService {
  constructor() {
    this.connections = {};
    this.listeners = {};
    this.reconnectTimeouts = {};
    this.pingIntervals = {};
    this.maxReconnectAttempts = 5;
    this.reconnectAttempts = {};
    this.reconnectDelay = 2000; // Start with 2 seconds
  }

  /**
   * Connect to a WebSocket channel
   * 
   * @param {string} channel - The channel to connect to (positions, accounts, risk-metrics, alerts)
   * @param {function} onMessage - Callback function for received messages
   * @param {function} onStatusChange - Callback function for connection status changes
   * @returns {Promise<boolean>} - Promise that resolves to true if connection is successful
   */
  connect(channel, onMessage, onStatusChange) {
    return new Promise((resolve, reject) => {
      if (!Object.values(Channels).includes(channel)) {
        const error = new Error(`Invalid channel: ${channel}`);
        if (onStatusChange) onStatusChange(ConnectionStatus.ERROR, error);
        reject(error);
        return;
      }

      // Update status to connecting
      if (onStatusChange) onStatusChange(ConnectionStatus.CONNECTING);

      // Initialize reconnect attempts counter
      this.reconnectAttempts[channel] = 0;

      // Create WebSocket connection
      const url = `${WS_BASE_URL}/${channel}`;
      const ws = new WebSocket(url);

      // Store connection and listeners
      this.connections[channel] = ws;
      this.listeners[channel] = {
        onMessage,
        onStatusChange
      };

      // Set up event handlers
      ws.onopen = () => {
        console.log(`Connected to ${channel} WebSocket`);
        if (onStatusChange) onStatusChange(ConnectionStatus.CONNECTED);
        
        // Reset reconnect attempts on successful connection
        this.reconnectAttempts[channel] = 0;
        
        // Send initial message to keep connection alive
        ws.send('subscribe');
        
        // Set up ping interval to keep connection alive
        this.pingIntervals[channel] = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000); // Send ping every 30 seconds
        
        resolve(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) onMessage(data);
        } catch (error) {
          console.error(`Error parsing ${channel} WebSocket message:`, error);
        }
      };

      ws.onclose = (event) => {
        console.log(`Disconnected from ${channel} WebSocket:`, event.code, event.reason);
        if (onStatusChange) onStatusChange(ConnectionStatus.DISCONNECTED);
        
        // Clear ping interval
        if (this.pingIntervals[channel]) {
          clearInterval(this.pingIntervals[channel]);
          delete this.pingIntervals[channel];
        }
        
        // Attempt to reconnect if not closed cleanly
        if (!event.wasClean) {
          this._scheduleReconnect(channel);
        }
      };

      ws.onerror = (error) => {
        console.error(`Error with ${channel} WebSocket:`, error);
        if (onStatusChange) onStatusChange(ConnectionStatus.ERROR, error);
        reject(error);
      };
    });
  }

  /**
   * Disconnect from a WebSocket channel
   * 
   * @param {string} channel - The channel to disconnect from
   */
  disconnect(channel) {
    if (this.connections[channel]) {
      // Clear reconnect timeout if exists
      if (this.reconnectTimeouts[channel]) {
        clearTimeout(this.reconnectTimeouts[channel]);
        delete this.reconnectTimeouts[channel];
      }
      
      // Clear ping interval
      if (this.pingIntervals[channel]) {
        clearInterval(this.pingIntervals[channel]);
        delete this.pingIntervals[channel];
      }
      
      // Close connection
      if (this.connections[channel].readyState === WebSocket.OPEN) {
        this.connections[channel].close();
      }
      
      delete this.connections[channel];
      delete this.listeners[channel];
      delete this.reconnectAttempts[channel];
      
      console.log(`Disconnected from ${channel} WebSocket`);
    }
  }

  /**
   * Disconnect from all WebSocket channels
   */
  disconnectAll() {
    Object.keys(this.connections).forEach(channel => {
      this.disconnect(channel);
    });
  }

  /**
   * Check if connected to a specific channel
   * 
   * @param {string} channel - The channel to check
   * @returns {boolean} - True if connected
   */
  isConnected(channel) {
    return (
      this.connections[channel] && 
      this.connections[channel].readyState === WebSocket.OPEN
    );
  }

  /**
   * Schedule a reconnection attempt for a channel
   * 
   * @private
   * @param {string} channel - The channel to reconnect to
   */
  _scheduleReconnect(channel) {
    // Increment reconnect attempts
    this.reconnectAttempts[channel] = (this.reconnectAttempts[channel] || 0) + 1;
    
    // Check if max attempts reached
    if (this.reconnectAttempts[channel] > this.maxReconnectAttempts) {
      console.log(`Max reconnect attempts reached for ${channel} WebSocket`);
      if (this.listeners[channel]?.onStatusChange) {
        this.listeners[channel].onStatusChange(ConnectionStatus.ERROR, new Error('Max reconnect attempts reached'));
      }
      return;
    }
    
    // Calculate exponential backoff delay
    const delay = Math.min(
      30000, // Max 30 seconds
      this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts[channel] - 1)
    );
    
    console.log(`Scheduling reconnect for ${channel} WebSocket in ${delay}ms (attempt ${this.reconnectAttempts[channel]})`);
    
    // Schedule reconnect
    this.reconnectTimeouts[channel] = setTimeout(() => {
      if (this.listeners[channel]) {
        this.connect(
          channel, 
          this.listeners[channel].onMessage, 
          this.listeners[channel].onStatusChange
        ).catch(error => {
          console.error(`Error reconnecting to ${channel} WebSocket:`, error);
        });
      }
    }, delay);
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService; 