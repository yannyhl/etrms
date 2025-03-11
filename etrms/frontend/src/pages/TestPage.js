import React, { useState } from 'react';
import { Box, Typography, Button, Paper, TextField, Alert } from '@mui/material';
import axios from 'axios';

/**
 * Test Page Component
 * 
 * This component provides a simple test page that can be accessed without authentication.
 */
const TestPage = () => {
  const [testResult, setTestResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin');

  const testBackendConnection = async () => {
    setLoading(true);
    setError(null);
    setTestResult(null);

    try {
      // Test the root endpoint
      const rootResponse = await axios.get('http://localhost:8000/');
      
      // Test the token endpoint
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const tokenResponse = await axios.post('http://localhost:8000/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      setTestResult({
        rootResponse: rootResponse.data,
        tokenResponse: tokenResponse.data
      });
    } catch (err) {
      console.error('Test error:', err);
      setError(err.message || 'An error occurred during the test');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        ETRMS Test Page
      </Typography>
      
      <Typography variant="body1" paragraph>
        This page is used to test the connection to the backend API.
      </Typography>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Test Backend Connection
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <TextField
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            fullWidth
            margin="normal"
          />
          <TextField
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            margin="normal"
            type="password"
          />
        </Box>
        
        <Button 
          variant="contained" 
          onClick={testBackendConnection}
          disabled={loading}
        >
          {loading ? 'Testing...' : 'Test Connection'}
        </Button>
        
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        
        {testResult && (
          <Box sx={{ mt: 2 }}>
            <Alert severity="success">
              Connection successful!
            </Alert>
            
            <Typography variant="h6" sx={{ mt: 2 }}>
              Root Response:
            </Typography>
            <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
              <pre>{JSON.stringify(testResult.rootResponse, null, 2)}</pre>
            </Paper>
            
            <Typography variant="h6" sx={{ mt: 2 }}>
              Token Response:
            </Typography>
            <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
              <pre>{JSON.stringify(testResult.tokenResponse, null, 2)}</pre>
            </Paper>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default TestPage; 