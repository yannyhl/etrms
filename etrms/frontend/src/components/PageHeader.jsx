import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import PropTypes from 'prop-types';

/**
 * PageHeader component for displaying consistent page headers across the application
 * 
 * @param {Object} props - Component props
 * @param {string} props.title - The main title of the page
 * @param {string} [props.description] - Optional description text for the page
 * @param {React.ReactNode} [props.actions] - Optional actions to display in the header (buttons, etc.)
 * @returns {React.ReactElement} The PageHeader component
 */
const PageHeader = ({ title, description, actions }) => {
  return (
    <Paper 
      elevation={0}
      sx={{
        mb: 4,
        p: 3,
        backgroundColor: 'background.default',
        borderRadius: 2
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          width: '100%'
        }}
      >
        <Box>
          <Typography variant="h4" component="h1" gutterBottom={!!description}>
            {title}
          </Typography>
          {description && (
            <Typography variant="subtitle1" color="text.secondary">
              {description}
            </Typography>
          )}
        </Box>
        
        {actions && (
          <Box 
            sx={{ 
              mt: { xs: 2, sm: 0 },
              display: 'flex',
              gap: 1
            }}
          >
            {actions}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

PageHeader.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
  actions: PropTypes.node
};

export default PageHeader; 