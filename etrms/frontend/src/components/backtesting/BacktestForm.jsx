import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  FormControl,
  FormHelperText,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  Autocomplete,
  Chip,
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { api } from '../../services/api';
import { handleApiError } from '../../utils/errorHandler';
import { useAlert } from '../../hooks/useAlert';
import AlertMessage from '../AlertMessage';

// Default backtest configuration
const DEFAULT_BACKTEST = {
  name: '',
  description: '',
  type: 'standard',
  start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
  end_date: new Date(),
  exchanges: [],
  symbols: [],
  timeframe: '1h',
  initial_capital: 10000,
  circuit_breakers: [],
  parameters: {},
};

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

// Backtest type options
const BACKTEST_TYPE_OPTIONS = [
  { value: 'standard', label: 'Standard Backtest' },
  { value: 'monte_carlo', label: 'Monte Carlo Simulation' },
  { value: 'walk_forward', label: 'Walk-Forward Analysis' },
  { value: 'optimization', label: 'Parameter Optimization' },
];

/**
 * Component for creating new backtests
 * 
 * @param {Object} props - Component props
 * @param {Function} props.onBacktestCreated - Function to call when a backtest is created
 * @returns {React.ReactElement} The BacktestForm component
 */
const BacktestForm = ({ onBacktestCreated }) => {
  const [formData, setFormData] = useState(DEFAULT_BACKTEST);
  const [loading, setLoading] = useState(false);
  const [exchanges, setExchanges] = useState([]);
  const [symbols, setSymbols] = useState([
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT',
    'DOGEUSDT', 'XRPUSDT', 'DOTUSDT', 'AVAXUSDT', 'MATICUSDT',
  ]);
  const { alert, showSuccess, showError, closeAlert } = useAlert();

  // Fetch exchanges on component mount
  useEffect(() => {
    fetchExchanges();
  }, []);

  // Fetch exchanges from the API
  const fetchExchanges = async () => {
    try {
      const response = await api.get('/accounts/exchanges');
      setExchanges(response.data);
    } catch (error) {
      handleApiError(error, 'BacktestForm.fetchExchanges', showError);
    }
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Handle date changes
  const handleDateChange = (name, value) => {
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Handle exchanges selection
  const handleExchangesChange = (event, newValue) => {
    setFormData((prev) => ({
      ...prev,
      exchanges: newValue.map((exchange) => exchange.id),
    }));
  };

  // Handle symbols selection
  const handleSymbolsChange = (event, newValue) => {
    setFormData((prev) => ({
      ...prev,
      symbols: newValue,
    }));
  };

  // Validate form data
  const validateForm = () => {
    if (!formData.name.trim()) {
      showError('Please enter a name for the backtest');
      return false;
    }

    if (formData.exchanges.length === 0) {
      showError('Please select at least one exchange');
      return false;
    }

    if (formData.symbols.length === 0) {
      showError('Please select at least one symbol');
      return false;
    }

    if (formData.start_date >= formData.end_date) {
      showError('Start date must be before end date');
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
      const response = await api.post('/backtest', formData);
      showSuccess('Backtest created successfully');
      setFormData(DEFAULT_BACKTEST);
      onBacktestCreated(response.data.id);
    } catch (error) {
      handleApiError(error, 'BacktestForm.handleSubmit', showError);
    } finally {
      setLoading(false);
    }
  };

  // Handle form reset
  const handleReset = () => {
    setFormData(DEFAULT_BACKTEST);
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Create New Backtest
        </Typography>

        <AlertMessage
          open={alert.open}
          type={alert.type}
          message={alert.message}
          onClose={closeAlert}
        />

        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {/* Basic Information */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Basic Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                name="name"
                label="Backtest Name"
                value={formData.name}
                onChange={handleInputChange}
                fullWidth
                required
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Backtest Type</InputLabel>
                <Select
                  name="type"
                  value={formData.type}
                  onChange={handleInputChange}
                  label="Backtest Type"
                >
                  {BACKTEST_TYPE_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                name="description"
                label="Description"
                value={formData.description}
                onChange={handleInputChange}
                fullWidth
                multiline
                rows={2}
              />
            </Grid>

            {/* Date Range */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Date Range
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12} md={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DateTimePicker
                  label="Start Date"
                  value={formData.start_date}
                  onChange={(value) => handleDateChange('start_date', value)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>

            <Grid item xs={12} md={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DateTimePicker
                  label="End Date"
                  value={formData.end_date}
                  onChange={(value) => handleDateChange('end_date', value)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Timeframe</InputLabel>
                <Select
                  name="timeframe"
                  value={formData.timeframe}
                  onChange={handleInputChange}
                  label="Timeframe"
                >
                  {TIMEFRAME_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                name="initial_capital"
                label="Initial Capital"
                type="number"
                value={formData.initial_capital}
                onChange={handleInputChange}
                fullWidth
                InputProps={{
                  startAdornment: '$',
                }}
              />
            </Grid>

            {/* Markets */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Markets
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12} md={6}>
              <Autocomplete
                multiple
                options={exchanges}
                getOptionLabel={(option) => option.name}
                value={exchanges.filter((exchange) =>
                  formData.exchanges.includes(exchange.id)
                )}
                onChange={handleExchangesChange}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Exchanges"
                    placeholder="Select exchanges"
                  />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      label={option.name}
                      {...getTagProps({ index })}
                      key={option.id}
                    />
                  ))
                }
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Autocomplete
                multiple
                options={symbols}
                value={formData.symbols}
                onChange={handleSymbolsChange}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Symbols"
                    placeholder="Select symbols"
                  />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      label={option}
                      {...getTagProps({ index })}
                      key={option}
                    />
                  ))
                }
                freeSolo
              />
            </Grid>

            {/* Submit Buttons */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  type="button"
                  variant="outlined"
                  color="secondary"
                  onClick={handleReset}
                  sx={{ mr: 2 }}
                  disabled={loading}
                >
                  Reset
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Create Backtest'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </CardContent>
    </Card>
  );
};

BacktestForm.propTypes = {
  onBacktestCreated: PropTypes.func.isRequired,
};

export default BacktestForm; 