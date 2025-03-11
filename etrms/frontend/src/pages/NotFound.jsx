import React from 'react';
import { Box, Button, Container, Typography } from '@mui/material';
import { Error as ErrorIcon } from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';

/**
 * NotFound page displayed when a user navigates to a route that doesn't exist
 */
const NotFound = () => {
  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '80vh',
          textAlign: 'center',
          py: 4,
        }}
      >
        <ErrorIcon sx={{ fontSize: 100, color: 'error.main', mb: 2 }} />
        
        <Typography variant="h1" component="h1" gutterBottom>
          404
        </Typography>
        
        <Typography variant="h4" component="h2" gutterBottom>
          Page Not Found
        </Typography>
        
        <Typography variant="body1" color="textSecondary" sx={{ mb: 4, maxWidth: 500 }}>
          The page you are looking for might have been removed, had its name changed,
          or is temporarily unavailable.
        </Typography>
        
        <Button
          component={RouterLink}
          to="/"
          variant="contained"
          color="primary"
          size="large"
        >
          Go to Dashboard
        </Button>
      </Box>
    </Container>
  );
};

export default NotFound; 