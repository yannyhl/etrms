import React, { Component } from 'react';
import { Box, Typography, Button, Paper, Container } from '@mui/material';
import { ErrorOutline as ErrorIcon } from '@mui/icons-material';

/**
 * ErrorBoundary component to catch JavaScript errors anywhere in the child component tree
 * and display a fallback UI instead of crashing the whole application
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to an error reporting service
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
    this.setState({ errorInfo });
    
    // You could also log to a monitoring service here
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ 
      hasError: false,
      error: null,
      errorInfo: null
    });
  }

  render() {
    if (this.state.hasError) {
      // Render fallback UI
      return (
        <Container maxWidth="md">
          <Paper 
            elevation={3}
            sx={{ 
              p: 4, 
              mt: 4, 
              textAlign: 'center',
              borderLeft: 5,
              borderColor: 'error.main'
            }}
          >
            <Box sx={{ mb: 2 }}>
              <ErrorIcon color="error" sx={{ fontSize: 60 }} />
            </Box>
            
            <Typography variant="h5" component="h2" gutterBottom>
              Something went wrong
            </Typography>
            
            <Typography variant="body1" color="textSecondary" paragraph>
              The application encountered an unexpected error. Please try again or contact support if the problem persists.
            </Typography>
            
            {this.state.error && (
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 2, 
                  mb: 3, 
                  bgcolor: 'grey.900',
                  maxHeight: '200px',
                  overflow: 'auto',
                  textAlign: 'left'
                }}
              >
                <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace' }}>
                  {this.state.error.toString()}
                </Typography>
              </Paper>
            )}
            
            <Box sx={{ mt: 3 }}>
              <Button 
                variant="contained" 
                color="primary" 
                onClick={this.handleReset}
                sx={{ mr: 2 }}
              >
                Try Again
              </Button>
              
              <Button 
                variant="outlined" 
                color="primary" 
                onClick={() => window.location.href = '/'}
              >
                Go to Dashboard
              </Button>
            </Box>
          </Paper>
        </Container>
      );
    }

    // If there's no error, render children normally
    return this.props.children;
  }
}

export default ErrorBoundary; 