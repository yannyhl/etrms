import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  Grid,
  Divider,
  Avatar,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import authService from '../services/authService';

/**
 * User Profile Page Component
 * 
 * This component displays and allows editing of the user's profile information.
 */
const Profile = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
  });
  
  const [errors, setErrors] = useState({});

  // Fetch user profile on component mount
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const userData = await authService.fetchUserProfile();
        setUser(userData);
        setFormData({
          ...formData,
          email: userData.email,
        });
      } catch (err) {
        console.error('Error fetching profile:', err);
        setError('Failed to load user profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
    
    // Clear field-specific error when user types
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: '',
      });
    }
  };

  // Validate form data
  const validateForm = () => {
    const newErrors = {};
    
    // Email validation
    if (formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    // Password validation (only if provided)
    if (formData.password) {
      if (formData.password.length < 6) {
        newErrors.password = 'Password must be at least 6 characters';
      }
      
      // Confirm password validation
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    // Check if anything has changed
    if (!formData.email && !formData.password) {
      setError('No changes to save');
      return;
    }
    
    setUpdating(true);
    
    try {
      // Prepare update data
      const updateData = {};
      
      if (formData.email && formData.email !== user.email) {
        updateData.email = formData.email;
      }
      
      if (formData.password) {
        updateData.password = formData.password;
      }
      
      // Update profile
      const updatedUser = await authService.updateProfile(updateData);
      setUser(updatedUser);
      
      // Clear password fields
      setFormData({
        ...formData,
        password: '',
        confirmPassword: '',
      });
      
      setSuccess('Profile updated successfully');
    } catch (err) {
      console.error('Update error:', err);
      
      // Handle different error scenarios
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An error occurred while updating your profile');
      }
    } finally {
      setUpdating(false);
    }
  };

  // Handle logout
  const handleLogout = () => {
    authService.logout();
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '80vh',
        }}
      >
        <CircularProgress size={40} />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Loading profile...
        </Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Avatar
            sx={{
              bgcolor: 'primary.main',
              width: 56,
              height: 56,
              mr: 2,
            }}
          >
            <PersonIcon fontSize="large" />
          </Avatar>
          <Box>
            <Typography variant="h4" gutterBottom>
              {user?.username}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {user?.role.charAt(0).toUpperCase() + user?.role.slice(1)} • Joined{' '}
              {new Date(user?.created_at).toLocaleDateString()}
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ mb: 4 }} />

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 3 }}>
            {success}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <Typography variant="h6" gutterBottom>
            Profile Information
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Username"
                value={user?.username || ''}
                disabled
                InputProps={{
                  readOnly: true,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                error={!!errors.email}
                helperText={errors.email}
                disabled={updating}
              />
            </Grid>
          </Grid>

          <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
            Change Password
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Leave blank if you don't want to change your password
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="New Password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                error={!!errors.password}
                helperText={errors.password}
                disabled={updating}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Confirm New Password"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                error={!!errors.confirmPassword}
                helperText={errors.confirmPassword}
                disabled={updating}
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
            <Button
              variant="outlined"
              color="error"
              onClick={handleLogout}
              disabled={updating}
            >
              Logout
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={updating}
            >
              {updating ? <CircularProgress size={24} /> : 'Save Changes'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default Profile; 