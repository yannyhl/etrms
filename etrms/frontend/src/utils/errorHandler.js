/**
 * Utility functions for handling errors in the frontend
 */

/**
 * Format an error message from an API error response
 * 
 * @param {Error} error - The error object from an API call
 * @returns {string} A formatted error message
 */
export const formatApiError = (error) => {
  if (!error) {
    return 'An unknown error occurred';
  }

  // Handle Axios error responses
  if (error.response) {
    const { status, data } = error.response;
    
    // Handle different status codes
    switch (status) {
      case 400:
        // Bad request - usually validation errors
        if (data.detail) {
          if (typeof data.detail === 'string') {
            return data.detail;
          }
          if (Array.isArray(data.detail)) {
            return data.detail.map(item => item.msg || item).join(', ');
          }
        }
        return 'Invalid request. Please check your input and try again.';
        
      case 401:
        return 'Authentication failed. Please log in again.';
        
      case 403:
        return 'You do not have permission to perform this action.';
        
      case 404:
        return 'The requested resource was not found.';
        
      case 409:
        return 'This operation could not be completed due to a conflict with the current state of the resource.';
        
      case 422:
        // Validation errors
        if (data.detail) {
          if (typeof data.detail === 'string') {
            return data.detail;
          }
          if (Array.isArray(data.detail)) {
            return data.detail.map(item => item.msg || item).join(', ');
          }
        }
        return 'Validation error. Please check your input and try again.';
        
      case 429:
        return 'Too many requests. Please try again later.';
        
      case 500:
      case 502:
      case 503:
      case 504:
        return 'Server error. Please try again later or contact support.';
        
      default:
        if (data && data.message) {
          return data.message;
        }
        if (data && data.detail) {
          return data.detail;
        }
        return `Error ${status}: ${data || 'Unknown error'}`;
    }
  }
  
  // Handle network errors
  if (error.request) {
    return 'Network error. Please check your internet connection and try again.';
  }
  
  // Handle other errors
  return error.message || 'An unexpected error occurred';
};

/**
 * Log an error to the console and potentially to a monitoring service
 * 
 * @param {Error} error - The error object
 * @param {string} context - The context in which the error occurred
 */
export const logError = (error, context = '') => {
  console.error(`Error in ${context}:`, error);
  
  // Here you could add integration with error monitoring services like Sentry
  // if (window.Sentry) {
  //   window.Sentry.captureException(error);
  //   window.Sentry.setContext('component', { name: context });
  // }
};

/**
 * Handle an API error by formatting it and optionally showing an alert
 * 
 * @param {Error} error - The error object from an API call
 * @param {string} context - The context in which the error occurred
 * @param {Function} setAlert - Function to set an alert message (optional)
 * @returns {string} A formatted error message
 */
export const handleApiError = (error, context = '', setAlert = null) => {
  logError(error, context);
  
  const errorMessage = formatApiError(error);
  
  if (setAlert) {
    setAlert({
      open: true,
      type: 'error',
      message: errorMessage
    });
  }
  
  return errorMessage;
};

/**
 * Create a retry function that will retry a function multiple times with exponential backoff
 * 
 * @param {Function} fn - The async function to retry
 * @param {Object} options - Options for retrying
 * @param {number} options.maxRetries - Maximum number of retries (default: 3)
 * @param {number} options.baseDelay - Base delay in ms (default: 1000)
 * @param {number} options.maxDelay - Maximum delay in ms (default: 10000)
 * @returns {Function} A function that will retry the original function
 */
export const createRetry = (fn, options = {}) => {
  const { 
    maxRetries = 3, 
    baseDelay = 1000, 
    maxDelay = 10000 
  } = options;
  
  return async (...args) => {
    let lastError;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn(...args);
      } catch (error) {
        lastError = error;
        
        // Don't retry on certain error codes
        if (error.response) {
          const { status } = error.response;
          if ([400, 401, 403, 404, 422].includes(status)) {
            throw error;
          }
        }
        
        if (attempt === maxRetries) {
          throw error;
        }
        
        // Calculate delay with exponential backoff and jitter
        const delay = Math.min(
          maxDelay,
          baseDelay * Math.pow(2, attempt) * (0.8 + Math.random() * 0.4)
        );
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw lastError;
  };
}; 