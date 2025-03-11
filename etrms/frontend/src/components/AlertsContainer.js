/**
 * Alerts Container Component
 * 
 * Manages and displays multiple alerts in a stack.
 */
import React, { useState, useEffect } from 'react';
import useWebSocket from '../hooks/useWebSocket';
import { Channels } from '../services/websocket';
import AlertNotification from './AlertNotification';

const AlertsContainer = () => {
  const [alerts, setAlerts] = useState([]);
  const { data: alertData, status, connect } = useWebSocket(Channels.ALERTS);
  
  // Add new alert when received from WebSocket
  useEffect(() => {
    if (alertData) {
      // Generate a unique ID for the alert
      const alertWithId = {
        ...alertData,
        id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      };
      
      // Add to alerts array
      setAlerts(prevAlerts => [alertWithId, ...prevAlerts].slice(0, 5)); // Keep only the 5 most recent alerts
    }
  }, [alertData]);
  
  // Remove an alert by ID
  const removeAlert = (id) => {
    setAlerts(prevAlerts => prevAlerts.filter(alert => alert.id !== id));
  };
  
  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 w-80">
      {alerts.map(alert => (
        <AlertNotification
          key={alert.id}
          alert={alert}
          onClose={() => removeAlert(alert.id)}
        />
      ))}
    </div>
  );
};

export default AlertsContainer; 