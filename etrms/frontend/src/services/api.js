import axios from 'axios';
import { logError, createRetry } from '../utils/errorHandler';

// Get the API base URL from environment variables or use a default
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Create an Axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to add the auth token to requests
api.interceptors.request.use(
  (config) => {
    // Get the token from localStorage
    const token = localStorage.getItem('etrms_token');
    const tokenType = localStorage.getItem('etrms_token_type');
    
    // If token exists, add it to the Authorization header
    if (token && tokenType) {
      config.headers.Authorization = `${tokenType} ${token}`;
    }
    
    return config;
  },
  (error) => {
    logError(error, 'API Request Interceptor');
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle authentication errors
    if (error.response && error.response.status === 401) {
      // Clear auth data from localStorage
      localStorage.removeItem('etrms_token');
      localStorage.removeItem('etrms_token_type');
      localStorage.removeItem('etrms_user');
      
      // Redirect to login page if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    
    // Handle server errors
    if (error.response && error.response.status >= 500) {
      logError(error, 'API Server Error');
    }
    
    // Handle network errors
    if (error.message === 'Network Error') {
      logError(error, 'API Network Error');
    }
    
    return Promise.reject(error);
  }
);

// Create retry-enabled API methods
const withRetry = createRetry(api.get);
const getWithRetry = (url, config) => withRetry(url, config);

// API service functions

/**
 * Get the current user profile
 * @returns {Promise} Promise with user data
 */
export const getUserProfile = () => {
  return api.get('/auth/me');
};

/**
 * Update the current user profile
 * @param {Object} userData - User data to update
 * @returns {Promise} Promise with updated user data
 */
export const updateUserProfile = (userData) => {
  return api.put('/auth/me', userData);
};

/**
 * Update the user's password
 * @param {Object} passwordData - Password data with current and new password
 * @returns {Promise} Promise with success message
 */
export const updatePassword = (passwordData) => {
  return api.put('/auth/password', passwordData);
};

/**
 * Get all API keys for the current user
 * @returns {Promise} Promise with API keys data
 */
export const getApiKeys = () => {
  return api.get('/auth/api-keys');
};

/**
 * Create a new API key
 * @param {Object} apiKeyData - API key data
 * @returns {Promise} Promise with created API key data
 */
export const createApiKey = (apiKeyData) => {
  return api.post('/auth/api-keys', apiKeyData);
};

/**
 * Update an existing API key
 * @param {string} apiKeyId - API key ID
 * @param {Object} apiKeyData - API key data to update
 * @returns {Promise} Promise with updated API key data
 */
export const updateApiKey = (apiKeyId, apiKeyData) => {
  return api.put(`/auth/api-keys/${apiKeyId}`, apiKeyData);
};

/**
 * Delete an API key
 * @param {string} apiKeyId - API key ID
 * @returns {Promise} Promise with success message
 */
export const deleteApiKey = (apiKeyId) => {
  return api.delete(`/auth/api-keys/${apiKeyId}`);
};

/**
 * Get all circuit breakers
 * @param {boolean} enabled - Filter by enabled status
 * @returns {Promise} Promise with circuit breakers data
 */
export const getCircuitBreakers = (enabled) => {
  const params = enabled !== undefined ? { enabled } : {};
  return api.get('/risk/circuit-breakers', { params });
};

/**
 * Create a new circuit breaker
 * @param {Object} circuitBreakerData - Circuit breaker data
 * @returns {Promise} Promise with created circuit breaker data
 */
export const createCircuitBreaker = (circuitBreakerData) => {
  return api.post('/risk/circuit-breakers', circuitBreakerData);
};

/**
 * Update an existing circuit breaker
 * @param {string} circuitBreakerId - Circuit breaker ID
 * @param {Object} circuitBreakerData - Circuit breaker data to update
 * @returns {Promise} Promise with updated circuit breaker data
 */
export const updateCircuitBreaker = (circuitBreakerId, circuitBreakerData) => {
  return api.put(`/risk/circuit-breakers/${circuitBreakerId}`, circuitBreakerData);
};

/**
 * Delete a circuit breaker
 * @param {string} circuitBreakerId - Circuit breaker ID
 * @returns {Promise} Promise with success message
 */
export const deleteCircuitBreaker = (circuitBreakerId) => {
  return api.delete(`/risk/circuit-breakers/${circuitBreakerId}`);
};

/**
 * Get circuit breaker events
 * @param {string} circuitBreakerId - Circuit breaker ID
 * @param {number} limit - Maximum number of events to return
 * @param {number} offset - Offset for pagination
 * @returns {Promise} Promise with circuit breaker events data
 */
export const getCircuitBreakerEvents = (circuitBreakerId, limit = 10, offset = 0) => {
  return api.get(`/risk/circuit-breakers/${circuitBreakerId}/events`, {
    params: { limit, offset }
  });
};

/**
 * Get all circuit breaker events
 * @param {number} limit - Maximum number of events to return
 * @param {number} offset - Offset for pagination
 * @returns {Promise} Promise with circuit breaker events data
 */
export const getAllCircuitBreakerEvents = (limit = 10, offset = 0) => {
  return api.get('/risk/circuit-breaker-events', {
    params: { limit, offset }
  });
};

/**
 * Get current risk metrics
 * @returns {Promise} Promise with risk metrics data
 */
export const getRiskMetrics = () => {
  // Use retry for risk metrics to handle temporary network issues
  return getWithRetry('/risk/metrics');
};

export const getExchanges = () => {
  return api.get('/accounts/exchanges');
};

export const getAccountSummary = () => {
  // Use retry for account summary to handle temporary network issues
  return getWithRetry('/accounts/summary');
}; 