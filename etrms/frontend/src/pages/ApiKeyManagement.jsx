import React, { useState, useEffect } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  FormControl,
  FormControlLabel,
  FormHelperText,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Key as KeyIcon,
} from '@mui/icons-material';
import { api } from '../services/api';
import { handleApiError } from '../utils/errorHandler';
import { useAlert } from '../hooks/useAlert';
import AlertMessage from '../components/AlertMessage';
import PageHeader from '../components/PageHeader';
import { formatDateTime } from '../utils/formatters';

// List of supported exchanges
const SUPPORTED_EXCHANGES = [
  { id: 'binance', name: 'Binance Futures' },
  { id: 'hyperliquid', name: 'Hyperliquid' },
];

// Default API key form data
const DEFAULT_API_KEY = {
  exchange: '',
  name: '',
  api_key: '',
  api_secret: '',
  passphrase: '',
  is_testnet: false,
  trading_enabled: true,
};

const ApiKeyManagement = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState(DEFAULT_API_KEY);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState(null);
  const [showSecret, setShowSecret] = useState(false);
  const [showPassphrase, setShowPassphrase] = useState(false);
  const { alert, showSuccess, showError, closeAlert } = useAlert();

  // Fetch API keys on component mount
  useEffect(() => {
    fetchApiKeys();
  }, []);

  // Fetch API keys from the backend
  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const response = await api.getApiKeys();
      setApiKeys(response.data);
    } catch (error) {
      handleApiError(error, 'ApiKeyManagement.fetchApiKeys', showError);
    } finally {
      setLoading(false);
    }
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Validate form data
  const validateForm = () => {
    const { exchange, name, api_key, api_secret } = formData;
    
    if (!exchange) {
      showError('Please select an exchange');
      return false;
    }
    
    if (!name) {
      showError('Please enter a name for this API key');
      return false;
    }
    
    if (!api_key) {
      showError('Please enter an API key');
      return false;
    }
    
    if (!api_secret) {
      showError('Please enter an API secret');
      return false;
    }
    
    // Check if passphrase is required for this exchange
    if (exchange === 'hyperliquid' && !formData.passphrase) {
      showError('Passphrase is required for Hyperliquid');
      return false;
    }
    
    return true;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      if (isEditing) {
        // Update existing API key
        await api.updateApiKey(editingId, formData);
        showSuccess('API key updated successfully');
      } else {
        // Create new API key
        await api.createApiKey(formData);
        showSuccess('API key added successfully');
      }
      
      // Reset form and fetch updated API keys
      setFormData(DEFAULT_API_KEY);
      setIsEditing(false);
      setEditingId(null);
      fetchApiKeys();
    } catch (error) {
      handleApiError(error, 'ApiKeyManagement.handleSubmit', showError);
    } finally {
      setLoading(false);
    }
  };

  // Handle edit button click
  const handleEdit = (apiKey) => {
    setFormData({
      exchange: apiKey.exchange,
      name: apiKey.name,
      api_key: apiKey.api_key,
      api_secret: '', // Don't populate for security reasons
      passphrase: '', // Don't populate for security reasons
      is_testnet: apiKey.is_testnet,
      trading_enabled: apiKey.trading_enabled
    });
    setIsEditing(true);
    setEditingId(apiKey.id);
  };

  // Handle delete button click
  const handleDeleteClick = (apiKey) => {
    setKeyToDelete(apiKey);
    setDeleteDialogOpen(true);
  };

  // Handle delete confirmation
  const handleDeleteConfirm = async () => {
    if (!keyToDelete) return;
    
    setLoading(true);
    try {
      await api.deleteApiKey(keyToDelete.id);
      showSuccess('API key deleted successfully');
      
      // Close dialog and fetch updated API keys
      setDeleteDialogOpen(false);
      setKeyToDelete(null);
      fetchApiKeys();
    } catch (error) {
      handleApiError(error, 'ApiKeyManagement.handleDeleteConfirm', showError);
    } finally {
      setLoading(false);
    }
  };

  // Handle form reset
  const handleReset = () => {
    setFormData(DEFAULT_API_KEY);
    setIsEditing(false);
    setEditingId(null);
  };

  // Toggle show/hide secret
  const toggleShowSecret = () => {
    setShowSecret(!showSecret);
  };

  // Toggle show/hide passphrase
  const toggleShowPassphrase = () => {
    setShowPassphrase(!showPassphrase);
  };

  return (
    <Container maxWidth="lg">
      <PageHeader
        title="API Key Management"
        description="Manage your exchange API keys for trading and risk monitoring."
      />

      <AlertMessage
        open={alert.open}
        type={alert.type}
        message={alert.message}
        onClose={closeAlert}
      />

      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Confirm Deletion</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the API key "{keyToDelete?.name}" for {
              SUPPORTED_EXCHANGES.find(e => e.id === keyToDelete?.exchange)?.name || keyToDelete?.exchange
            }?
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      <Grid container spacing={4}>
        <Grid item xs={12} md={5}>
          <Card>
            <CardHeader
              title={isEditing ? "Edit API Key" : "Add API Key"}
              subheader="Configure exchange API access for trading and monitoring"
            />
            <Divider />
            <CardContent>
              <form onSubmit={handleSubmit}>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Exchange</InputLabel>
                      <Select
                        name="exchange"
                        value={formData.exchange}
                        onChange={handleInputChange}
                        label="Exchange"
                        disabled={isEditing}
                      >
                        {SUPPORTED_EXCHANGES.map(exchange => (
                          <MenuItem key={exchange.id} value={exchange.id}>
                            {exchange.name}
                          </MenuItem>
                        ))}
                      </Select>
                      <FormHelperText>
                        Select the exchange for this API key
                      </FormHelperText>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      label="Name"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      fullWidth
                      required
                      helperText="A descriptive name for this API key"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      label="API Key"
                      name="api_key"
                      value={formData.api_key}
                      onChange={handleInputChange}
                      fullWidth
                      required
                      helperText="Your exchange API key"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      label="API Secret"
                      name="api_secret"
                      type={showSecret ? "text" : "password"}
                      value={formData.api_secret}
                      onChange={handleInputChange}
                      fullWidth
                      required
                      helperText={
                        isEditing
                          ? "Leave unchanged to keep the current secret"
                          : "Your exchange API secret"
                      }
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              onClick={toggleShowSecret}
                              edge="end"
                            >
                              {showSecret ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  </Grid>

                  {(formData.exchange === 'hyperliquid') && (
                    <Grid item xs={12}>
                      <TextField
                        label="Passphrase"
                        name="passphrase"
                        type={showPassphrase ? "text" : "password"}
                        value={formData.passphrase}
                        onChange={handleInputChange}
                        fullWidth
                        required={formData.exchange === 'hyperliquid'}
                        helperText={
                          isEditing
                            ? "Leave unchanged to keep the current passphrase"
                            : "Your exchange API passphrase"
                        }
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={toggleShowPassphrase}
                                edge="end"
                              >
                                {showPassphrase ? <VisibilityOffIcon /> : <VisibilityIcon />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                  )}

                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          name="is_testnet"
                          checked={formData.is_testnet}
                          onChange={handleInputChange}
                          color="primary"
                        />
                      }
                      label="Testnet"
                    />
                    <FormHelperText>
                      Use testnet/sandbox environment
                    </FormHelperText>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          name="trading_enabled"
                          checked={formData.trading_enabled}
                          onChange={handleInputChange}
                          color="primary"
                        />
                      }
                      label="Trading Enabled"
                    />
                    <FormHelperText>
                      Allow trading operations
                    </FormHelperText>
                  </Grid>

                  <Grid item xs={12}>
                    <Box display="flex" justifyContent="flex-end" gap={2}>
                      <Button
                        type="button"
                        onClick={handleReset}
                        disabled={loading}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        variant="contained"
                        color="primary"
                        startIcon={isEditing ? <EditIcon /> : <AddIcon />}
                        disabled={loading}
                      >
                        {loading ? (
                          <CircularProgress size={24} />
                        ) : isEditing ? (
                          "Update API Key"
                        ) : (
                          "Add API Key"
                        )}
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </form>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={7}>
          <Card>
            <CardHeader
              title="Your API Keys"
              subheader="Manage your exchange API keys"
            />
            <Divider />
            <CardContent>
              {loading && !apiKeys.length && (
                <Box display="flex" justifyContent="center" py={3}>
                  <CircularProgress />
                </Box>
              )}

              {!loading && !apiKeys.length && (
                <Alert severity="info">
                  You haven't added any API keys yet. Add an API key to start monitoring your trading accounts.
                </Alert>
              )}

              {apiKeys.length > 0 && (
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Exchange</TableCell>
                        <TableCell>API Key</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {apiKeys.map((apiKey) => (
                        <TableRow key={apiKey.id}>
                          <TableCell>
                            <Box display="flex" alignItems="center">
                              <KeyIcon sx={{ mr: 1, color: 'primary.main' }} />
                              <Typography variant="body2">{apiKey.name}</Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            {SUPPORTED_EXCHANGES.find(e => e.id === apiKey.exchange)?.name || apiKey.exchange}
                          </TableCell>
                          <TableCell>
                            <Tooltip title={apiKey.api_key}>
                              <Typography variant="body2">
                                {apiKey.api_key.substring(0, 8)}...
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Box display="flex" flexDirection="column" gap={0.5}>
                              <Chip
                                size="small"
                                label={apiKey.is_testnet ? "Testnet" : "Mainnet"}
                                color={apiKey.is_testnet ? "warning" : "primary"}
                                variant="outlined"
                              />
                              <Chip
                                size="small"
                                label={apiKey.trading_enabled ? "Trading Enabled" : "Read Only"}
                                color={apiKey.trading_enabled ? "success" : "default"}
                                variant="outlined"
                              />
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box display="flex">
                              <IconButton
                                color="primary"
                                onClick={() => handleEdit(apiKey)}
                                disabled={loading}
                                size="small"
                              >
                                <EditIcon />
                              </IconButton>
                              <IconButton
                                color="error"
                                onClick={() => handleDeleteClick(apiKey)}
                                disabled={loading}
                                size="small"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ApiKeyManagement; 