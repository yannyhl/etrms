/**
 * Authentication Service
 * 
 * This service handles authentication-related operations such as login, registration,
 * and token management.
 */
import axios from 'axios';

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Debug log
console.log('Auth Service API URL:', API_URL);

// Token storage key
const TOKEN_KEY = 'etrms_auth_token';
const USER_KEY = 'etrms_user';

/**
 * Get the stored authentication token
 * @returns {string|null} The authentication token or null if not found
 */
const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Set the authentication token in local storage
 * @param {string} token - The authentication token to store
 */
const setToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * Remove the authentication token from local storage
 */
const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

/**
 * Get the stored user information
 * @returns {Object|null} The user object or null if not found
 */
const getUser = () => {
  const userStr = localStorage.getItem(USER_KEY);
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch (e) {
      console.error('Error parsing user data:', e);
      return null;
    }
  }
  return null;
};

/**
 * Set the user information in local storage
 * @param {Object} user - The user object to store
 */
const setUser = (user) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

/**
 * Check if the user is authenticated
 * @returns {boolean} True if the user is authenticated, false otherwise
 */
const isAuthenticated = () => {
  return !!getToken();
};

/**
 * Configure axios with authentication headers
 */
const configureAxios = () => {
  axios.interceptors.request.use(
    (config) => {
      const token = getToken();
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response && error.response.status === 401) {
        // Unauthorized, clear token and redirect to login
        removeToken();
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );
};

/**
 * Login with username and password
 * @param {string} username - The username or email
 * @param {string} password - The password
 * @returns {Promise<Object>} The login response
 */
const login = async (username, password) => {
  try {
    console.log('Login attempt for user:', username);
    
    // Use URLSearchParams to format the request body as form data
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    console.log('Login request URL:', `${API_URL}/token`);
    console.log('Login request headers:', {
      'Content-Type': 'application/x-www-form-urlencoded',
    });
    
    const response = await axios.post(`${API_URL}/token`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    console.log('Login response:', response.data);
    
    if (response.data.access_token) {
      setToken(response.data.access_token);
      
      // Since we're using a simplified backend, create a mock user profile
      const mockUser = {
        username: username,
        email: `${username}@example.com`,
        full_name: username.charAt(0).toUpperCase() + username.slice(1),
        is_active: true
      };
      setUser(mockUser);
    }
    
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    console.error('Login error details:', {
      message: error.message,
      response: error.response ? {
        status: error.response.status,
        data: error.response.data
      } : 'No response',
      request: error.request ? 'Request made but no response received' : 'No request made'
    });
    throw error;
  }
};

/**
 * Register a new user
 * @param {string} username - The username
 * @param {string} email - The email
 * @param {string} password - The password
 * @returns {Promise<Object>} The registration response
 */
const register = async (username, email, password) => {
  try {
    // Since we're using a simplified backend without registration,
    // we'll just simulate a successful registration
    return {
      username,
      email,
      message: "Registration successful"
    };
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

/**
 * Fetch the user profile
 * @returns {Promise<Object>} The user profile
 */
const fetchUserProfile = async () => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Since we're using a simplified backend, return the stored user
    const user = getUser();
    if (user) {
      return user;
    }

    // If no user is stored, create a mock user
    const mockUser = {
      username: "admin",
      email: "admin@example.com",
      full_name: "Admin User",
      is_active: true
    };
    setUser(mockUser);
    return mockUser;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    throw error;
  }
};

/**
 * Update the user profile
 * @param {Object} userData - The updated user data
 * @returns {Promise<Object>} The updated user profile
 */
const updateProfile = async (userData) => {
  try {
    // Since we're using a simplified backend, just update the stored user
    setUser({...getUser(), ...userData});
    return userData;
  } catch (error) {
    console.error('Error updating profile:', error);
    throw error;
  }
};

/**
 * Logout the user
 */
const logout = () => {
  removeToken();
  window.location.href = '/login';
};

// Initialize axios configuration
configureAxios();

const authService = {
  login,
  register,
  logout,
  getToken,
  getUser,
  isAuthenticated,
  fetchUserProfile,
  updateProfile,
};

export default authService; 