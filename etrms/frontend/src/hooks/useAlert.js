import { useState, useCallback } from 'react';

/**
 * Custom hook for managing alerts
 * 
 * @returns {Object} Alert state and functions
 */
export const useAlert = () => {
  const [alert, setAlert] = useState({
    open: false,
    type: 'info',
    message: '',
    title: '',
  });

  /**
   * Show an alert
   * 
   * @param {string} type - Alert type ('success', 'error', 'warning', 'info')
   * @param {string} message - Alert message
   * @param {string} [title] - Optional alert title
   */
  const showAlert = useCallback((type, message, title = '') => {
    setAlert({
      open: true,
      type,
      message,
      title,
    });
  }, []);

  /**
   * Show a success alert
   * 
   * @param {string} message - Alert message
   * @param {string} [title] - Optional alert title
   */
  const showSuccess = useCallback((message, title = '') => {
    showAlert('success', message, title);
  }, [showAlert]);

  /**
   * Show an error alert
   * 
   * @param {string} message - Alert message
   * @param {string} [title] - Optional alert title
   */
  const showError = useCallback((message, title = '') => {
    showAlert('error', message, title);
  }, [showAlert]);

  /**
   * Show a warning alert
   * 
   * @param {string} message - Alert message
   * @param {string} [title] - Optional alert title
   */
  const showWarning = useCallback((message, title = '') => {
    showAlert('warning', message, title);
  }, [showAlert]);

  /**
   * Show an info alert
   * 
   * @param {string} message - Alert message
   * @param {string} [title] - Optional alert title
   */
  const showInfo = useCallback((message, title = '') => {
    showAlert('info', message, title);
  }, [showAlert]);

  /**
   * Close the alert
   */
  const closeAlert = useCallback(() => {
    setAlert(prev => ({
      ...prev,
      open: false,
    }));
  }, []);

  return {
    alert,
    setAlert,
    showAlert,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    closeAlert,
  };
}; 