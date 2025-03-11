import React, { useState, useEffect } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  FormHelperText,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Snackbar,
  TextField,
  Typography,
} from '@mui/material';
import { Save as SaveIcon, LockReset as LockResetIcon } from '@mui/icons-material';
import { api } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import PageHeader from '../components/PageHeader';

// Theme options
const THEME_OPTIONS = [
  { value: 'dark', label: 'Dark Theme' },
  { value: 'light', label: 'Light Theme' },
];

// Timeframe options
const TIMEFRAME_OPTIONS = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '30m', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '1w', label: '1 Week' },
];

const Settings = () => {
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState({
    theme: 'dark',
    default_exchange: '',
    default_timeframe: '1h',
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [alert, setAlert] = useState({ open: false, type: 'success', message: '' });
  const [exchanges, setExchanges] = useState([]);

  // Load user data on mount
  useEffect(() => {
    if (user) {
      setProfileData({
        theme: user.theme || 'dark',
        default_exchange: user.default_exchange || '',
        default_timeframe: user.default_timeframe || '1h',
      });
    }
    
    // Fetch available exchanges
    fetchExchanges();
  }, [user]);

  const fetchExchanges = async () => {
    try {
      const response = await api.get('/accounts/exchanges');
      setExchanges(response.data);
    } catch (error) {
      console.error('Error fetching exchanges:', error);
      showAlert('error', 'Failed to load exchanges');
    }
  };

  const showAlert = (type, message) => {
    setAlert({ open: true, type, message });
  };

  const handleAlertClose = () => {
    setAlert({ ...alert, open: false });
  };

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
  };

  const validateProfileForm = () => {
    // Simple validation for profile form
    return true;
  };

  const validatePasswordForm = () => {
    if (!passwordData.current_password) {
      showAlert('error', 'Current password is required');
      return false;
    }

    if (!passwordData.new_password) {
      showAlert('error', 'New password is required');
      return false;
    }

    if (passwordData.new_password.length < 8) {
      showAlert('error', 'New password must be at least 8 characters');
      return false;
    }

    if (passwordData.new_password !== passwordData.confirm_password) {
      showAlert('error', 'Passwords do not match');
      return false;
    }

    return true;
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();

    if (!validateProfileForm()) return;

    setLoading(true);
    try {
      const response = await api.put('/auth/me', profileData);
      updateUser(response.data);
      showAlert('success', 'Profile updated successfully');
    } catch (error) {
      console.error('Error updating profile:', error);
      showAlert('error', 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();

    if (!validatePasswordForm()) return;

    setLoading(true);
    try {
      await api.put('/auth/password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      
      // Reset password fields
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
      
      showAlert('success', 'Password updated successfully');
    } catch (error) {
      console.error('Error updating password:', error);
      if (error.response && error.response.status === 401) {
        showAlert('error', 'Current password is incorrect');
      } else {
        showAlert('error', 'Failed to update password');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <PageHeader
        title="Settings"
        description="Manage your account settings and preferences."
      />

      <Snackbar
        open={alert.open}
        autoHideDuration={6000}
        onClose={handleAlertClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleAlertClose} severity={alert.type}>
          {alert.message}
        </Alert>
      </Snackbar>

      <Grid container spacing={4}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Profile Settings"
              subheader="Update your profile and preferences"
            />
            <Divider />
            <CardContent>
              <form onSubmit={handleProfileSubmit}>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      Username
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      {user?.username || 'Loading...'}
                    </Typography>
                  </Grid>

                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Theme</InputLabel>
                      <Select
                        name="theme"
                        value={profileData.theme}
                        onChange={handleProfileChange}
                        label="Theme"
                      >
                        {THEME_OPTIONS.map(option => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                      <FormHelperText>
                        Choose your preferred theme
                      </FormHelperText>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Default Exchange</InputLabel>
                      <Select
                        name="default_exchange"
                        value={profileData.default_exchange}
                        onChange={handleProfileChange}
                        label="Default Exchange"
                      >
                        <MenuItem value="">
                          <em>None</em>
                        </MenuItem>
                        {exchanges.map(exchange => (
                          <MenuItem key={exchange.id} value={exchange.id}>
                            {exchange.name}
                          </MenuItem>
                        ))}
                      </Select>
                      <FormHelperText>
                        Choose your default exchange
                      </FormHelperText>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Default Timeframe</InputLabel>
                      <Select
                        name="default_timeframe"
                        value={profileData.default_timeframe}
                        onChange={handleProfileChange}
                        label="Default Timeframe"
                      >
                        {TIMEFRAME_OPTIONS.map(option => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                      <FormHelperText>
                        Choose your default chart timeframe
                      </FormHelperText>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12}>
                    <Box display="flex" justifyContent="flex-end">
                      <Button
                        type="submit"
                        variant="contained"
                        color="primary"
                        startIcon={<SaveIcon />}
                        disabled={loading}
                      >
                        {loading ? <CircularProgress size={24} /> : 'Save Changes'}
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </form>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Change Password"
              subheader="Update your password"
            />
            <Divider />
            <CardContent>
              <form onSubmit={handlePasswordSubmit}>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      label="Current Password"
                      name="current_password"
                      type="password"
                      value={passwordData.current_password}
                      onChange={handlePasswordChange}
                      fullWidth
                      required
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      label="New Password"
                      name="new_password"
                      type="password"
                      value={passwordData.new_password}
                      onChange={handlePasswordChange}
                      fullWidth
                      required
                      helperText="Password must be at least 8 characters"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      label="Confirm New Password"
                      name="confirm_password"
                      type="password"
                      value={passwordData.confirm_password}
                      onChange={handlePasswordChange}
                      fullWidth
                      required
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Box display="flex" justifyContent="flex-end">
                      <Button
                        type="submit"
                        variant="contained"
                        color="primary"
                        startIcon={<LockResetIcon />}
                        disabled={loading}
                      >
                        {loading ? <CircularProgress size={24} /> : 'Change Password'}
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </form>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Settings; 