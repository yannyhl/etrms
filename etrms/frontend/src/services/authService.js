/**
 * Authentication Service
 * 
 * This service handles authentication-related operations such as login, registration,
 * and token management.
 */
import axios from 'axios';

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

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
    // Use URLSearchParams to format the request body as form data
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await axios.post(`${API_URL}/auth/login`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    if (response.data.access_token) {
      setToken(response.data.access_token);
      
      // Fetch user profile
      await fetchUserProfile();
    }

    return response.data;
  } catch (error) {
    console.error('Login error:', error);
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
    const response = await axios.post(`${API_URL}/auth/register`, {
      username,
      email,
      password,
    });
    return response.data;
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

    const response = await axios.get(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    // Store user data
    setUser(response.data);
    return response.data;
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
    const response = await axios.put(`${API_URL}/auth/me`, userData, {
      headers: {
        Authorization: `Bearer ${getToken()}`,
      },
    });
    
    // Update stored user data
    setUser(response.data);
    return response.data;
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