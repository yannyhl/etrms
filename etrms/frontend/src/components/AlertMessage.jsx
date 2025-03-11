import React from 'react';
import PropTypes from 'prop-types';
import { Snackbar, Alert, AlertTitle } from '@mui/material';

/**
 * AlertMessage component for displaying alerts and notifications
 * 
 * @param {Object} props - Component props
 * @param {boolean} props.open - Whether the alert is open
 * @param {string} props.type - Alert type ('success', 'error', 'warning', 'info')
 * @param {string} props.message - Alert message
 * @param {string} [props.title] - Optional alert title
 * @param {Function} props.onClose - Function to call when the alert is closed
 * @param {Object} [props.anchorOrigin] - Position of the alert
 * @param {number} [props.autoHideDuration] - Duration in ms before the alert auto-hides
 * @returns {React.ReactElement} The AlertMessage component
 */
const AlertMessage = ({
  open,
  type,
  message,
  title,
  onClose,
  anchorOrigin = { vertical: 'top', horizontal: 'center' },
  autoHideDuration = 6000,
}) => {
  if (!message) return null;

  return (
    <Snackbar
      open={open}
      autoHideDuration={autoHideDuration}
      onClose={onClose}
      anchorOrigin={anchorOrigin}
    >
      <Alert
        onClose={onClose}
        severity={type}
        variant="filled"
        sx={{ width: '100%' }}
      >
        {title && <AlertTitle>{title}</AlertTitle>}
        {message}
      </Alert>
    </Snackbar>
  );
};

AlertMessage.propTypes = {
  open: PropTypes.bool.isRequired,
  type: PropTypes.oneOf(['success', 'error', 'warning', 'info']).isRequired,
  message: PropTypes.string.isRequired,
  title: PropTypes.string,
  onClose: PropTypes.func.isRequired,
  anchorOrigin: PropTypes.shape({
    vertical: PropTypes.oneOf(['top', 'bottom']),
    horizontal: PropTypes.oneOf(['left', 'center', 'right']),
  }),
  autoHideDuration: PropTypes.number,
};

export default AlertMessage; 