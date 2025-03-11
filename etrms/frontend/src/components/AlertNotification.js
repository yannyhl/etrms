/**
 * Alert Notification Component
 * 
 * Displays circuit breaker alerts and other notifications.
 */
import React, { useState, useEffect } from 'react';

const AlertNotification = ({ alert, onClose }) => {
  const [isVisible, setIsVisible] = useState(true);
  
  // Auto-close the alert after 10 seconds
  useEffect(() => {
    if (!alert) return;
    
    const timer = setTimeout(() => {
      setIsVisible(false);
      if (onClose) setTimeout(onClose, 300); // Allow animation to complete
    }, 10000);
    
    return () => clearTimeout(timer);
  }, [alert, onClose]);
  
  // Handle manual close
  const handleClose = () => {
    setIsVisible(false);
    if (onClose) setTimeout(onClose, 300); // Allow animation to complete
  };
  
  if (!alert) return null;
  
  // Format timestamp
  const timestamp = new Date(alert.triggered_at * 1000).toLocaleTimeString();
  
  // Determine alert type styling
  const getAlertStyle = () => {
    if (alert.type === 'circuit_breaker') {
      return {
        bgColor: 'bg-red-50',
        borderColor: 'border-red-400',
        textColor: 'text-red-800',
        iconColor: 'text-red-400',
        icon: (
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        )
      };
    }
    
    return {
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-400',
      textColor: 'text-blue-800',
      iconColor: 'text-blue-400',
      icon: (
        <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
      )
    };
  };
  
  const { bgColor, borderColor, textColor, iconColor, icon } = getAlertStyle();
  
  return (
    <div 
      className={`rounded-md border ${borderColor} ${bgColor} p-4 transition-all duration-300 ease-in-out ${isVisible ? 'opacity-100' : 'opacity-0 transform translate-y-2'}`}
    >
      <div className="flex">
        <div className={`flex-shrink-0 ${iconColor}`}>
          {icon}
        </div>
        <div className="ml-3">
          <h3 className={`text-sm font-medium ${textColor}`}>
            {alert.description}
          </h3>
          <div className={`mt-2 text-sm ${textColor}`}>
            <p>
              <span className="font-semibold">{alert.exchange}</span> - <span className="font-semibold">{alert.symbol}</span>
            </p>
            <p className="mt-1 text-xs">
              {timestamp} - {alert.condition_name}
            </p>
            {alert.context && (
              <div className="mt-1 text-xs">
                {Object.entries(alert.context).map(([key, value]) => (
                  <div key={key}>
                    <span className="font-medium">{key.replace(/_/g, ' ')}:</span> {typeof value === 'number' ? value.toFixed(2) : value}
                  </div>
                ))}
              </div>
            )}
            {alert.action_result && (
              <p className="mt-1 font-medium">
                Action: {alert.action_result}
              </p>
            )}
          </div>
        </div>
        <div className="ml-auto pl-3">
          <div className="-mx-1.5 -my-1.5">
            <button
              type="button"
              onClick={handleClose}
              className={`inline-flex rounded-md p-1.5 ${bgColor} ${textColor} hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-50 focus:ring-gray-600`}
            >
              <span className="sr-only">Dismiss</span>
              <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertNotification; 