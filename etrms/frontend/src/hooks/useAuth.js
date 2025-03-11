import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { api } from '../services/api';

// Create a context for authentication
const AuthContext = createContext(null);

// Token storage keys
const TOKEN_KEY = 'etrms_token';
const TOKEN_TYPE_KEY = 'etrms_token_type';
const USER_KEY = 'etrms_user';

// Provider component that wraps the app and makes auth available to any child component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem(TOKEN_KEY);
        const tokenType = localStorage.getItem(TOKEN_TYPE_KEY);
        const storedUser = localStorage.getItem(USER_KEY);

        if (token && tokenType) {
          // Set the authorization header for all future requests
          api.defaults.headers.common['Authorization'] = `${tokenType} ${token}`;

          // If we have a stored user, use it
          if (storedUser) {
            setUser(JSON.parse(storedUser));
          } else {
            // Otherwise, fetch the user profile
            try {
              const response = await api.get('/auth/me');
              const userData = response.data;
              setUser(userData);
              localStorage.setItem(USER_KEY, JSON.stringify(userData));
            } catch (error) {
              console.error('Error fetching user profile:', error);
              // If we can't fetch the user, clear the auth state
              logout();
            }
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
      } finally {
        setLoading(false);
        setInitialized(true);
      }
    };

    initAuth();
  }, []);

  // Login function
  const login = useCallback((token, tokenType) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(TOKEN_TYPE_KEY, tokenType);

    // Set the authorization header for all future requests
    api.defaults.headers.common['Authorization'] = `${tokenType} ${token}`;

    // Fetch the user profile
    api.get('/auth/me')
      .then(response => {
        const userData = response.data;
        setUser(userData);
        localStorage.setItem(USER_KEY, JSON.stringify(userData));
      })
      .catch(error => {
        console.error('Error fetching user profile:', error);
        // If we can't fetch the user, clear the auth state
        logout();
      });
  }, []);

  // Logout function
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_TYPE_KEY);
    localStorage.removeItem(USER_KEY);
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  }, []);

  // Check if the user is authenticated
  const isAuthenticated = useCallback(() => {
    return !!localStorage.getItem(TOKEN_KEY);
  }, []);

  // Get the current user
  const getUser = useCallback(() => {
    const storedUser = localStorage.getItem(USER_KEY);
    return storedUser ? JSON.parse(storedUser) : null;
  }, []);

  // Update the user profile
  const updateUser = useCallback((userData) => {
    setUser(userData);
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
  }, []);

  // The value that will be provided to consumers of this context
  const value = {
    user,
    loading,
    initialized,
    login,
    logout,
    isAuthenticated,
    getUser,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook for components to get the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 