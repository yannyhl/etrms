import React, { useState, useEffect } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Checkbox,
  CircularProgress,
  Divider,
  FormControl,
  FormControlLabel,
  FormHelperText,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

import { formatDateTime } from '../utils/formatters';
import { api } from '../services/api';

const CONDITION_TYPES = [
  { value: 'max_drawdown', label: 'Maximum Drawdown', 
    description: 'Triggers when the drawdown exceeds a specified percentage',
    defaultThreshold: 10 },
  { value: 'max_position_size', label: 'Maximum Position Size', 
    description: 'Triggers when a position exceeds a percentage of account equity',
    defaultThreshold: 25 },
  { value: 'max_leverage', label: 'Maximum Leverage', 
    description: 'Triggers when the overall leverage exceeds a specified value',
    defaultThreshold: 5 },
  { value: 'max_exposure', label: 'Maximum Exposure', 
    description: 'Triggers when the total exposure exceeds a percentage of account equity',
    defaultThreshold: 80 },
  { value: 'daily_loss', label: 'Daily Loss', 
    description: 'Triggers when the daily loss exceeds a specified percentage',
    defaultThreshold: -5 },
];

const ACTION_TYPES = [
  { value: 'notify', label: 'Notify Only', 
    description: 'Send a notification without taking any action' },
  { value: 'reduce_position', label: 'Reduce Position', 
    description: 'Reduce the size of the position by a specified percentage',
    hasParams: true, 
    paramName: 'reduction_percentage', 
    paramLabel: 'Reduction Percentage',
    paramDefault: 50 },
  { value: 'close_position', label: 'Close Position', 
    description: 'Close the position completely',
    hasParams: true,
    paramName: 'close_all',
    paramLabel: 'Close All Positions',
    paramType: 'boolean',
    paramDefault: false },
  { value: 'pause_trading', label: 'Pause Trading', 
    description: 'Temporarily pause all trading activity' },
];

const DEFAULT_CIRCUIT_BREAKER = {
  name: '',
  description: '',
  condition: 'max_drawdown',
  action: 'notify',
  parameters: { threshold: 10 },
  symbols: [],
  exchanges: [],
  enabled: true,
};

const CircuitBreakerForm = ({ onBreakerCreated, onBreakerUpdated, onBreakerDeleted }) => {
  const [circuitBreakers, setCircuitBreakers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ ...DEFAULT_CIRCUIT_BREAKER });
  const [editMode, setEditMode] = useState(false);
  const [alert, setAlert] = useState({ open: false, type: 'success', message: '' });
  const [exchangeList, setExchangeList] = useState([]);
  const [symbolList, setSymbolList] = useState([]);
  
  // Fetch circuit breakers on mount
  useEffect(() => {
    fetchCircuitBreakers();
    fetchExchanges();
  }, []);
  
  const fetchCircuitBreakers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/risk/circuit-breakers');
      setCircuitBreakers(response.data);
    } catch (error) {
      showAlert('error', 'Failed to load circuit breakers');
      console.error('Error fetching circuit breakers:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchExchanges = async () => {
    try {
      const response = await api.get('/accounts/exchanges');
      setExchangeList(response.data);
    } catch (error) {
      console.error('Error fetching exchanges:', error);
    }
  };
  
  const fetchSymbols = async (exchangeId) => {
    try {
      const response = await api.get(`/accounts/exchanges/${exchangeId}/symbols`);
      setSymbolList(response.data);
    } catch (error) {
      console.error('Error fetching symbols:', error);
    }
  };
  
  const showAlert = (type, message) => {
    setAlert({ open: true, type, message });
  };
  
  const handleAlertClose = () => {
    setAlert({ ...alert, open: false });
  };
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };
  
  const handleConditionChange = (e) => {
    const condition = e.target.value;
    const selectedCondition = CONDITION_TYPES.find(type => type.value === condition);
    
    setFormData(prev => ({
      ...prev,
      condition,
      parameters: {
        ...prev.parameters,
        threshold: selectedCondition?.defaultThreshold || 10
      }
    }));
  };
  
  const handleActionChange = (e) => {
    const action = e.target.value;
    const selectedAction = ACTION_TYPES.find(type => type.value === action);
    
    let newParams = { ...formData.parameters };
    
    // Add default parameter for the selected action if it has parameters
    if (selectedAction?.hasParams) {
      newParams[selectedAction.paramName] = selectedAction.paramDefault;
    }
    
    setFormData(prev => ({
      ...prev,
      action,
      parameters: newParams
    }));
  };
  
  const handleParameterChange = (e) => {
    const { name, value, type, checked } = e.target;
    const finalValue = type === 'checkbox' ? checked : value;
    
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [name]: finalValue
      }
    }));
  };
  
  const handleSymbolsChange = (e) => {
    setFormData(prev => ({
      ...prev,
      symbols: Array.from(e.target.selectedOptions, option => option.value)
    }));
  };
  
  const handleExchangesChange = (e) => {
    const selectedExchanges = Array.from(e.target.selectedOptions, option => option.value);
    setFormData(prev => ({
      ...prev,
      exchanges: selectedExchanges
    }));
    
    // If only one exchange is selected, fetch its symbols
    if (selectedExchanges.length === 1) {
      fetchSymbols(selectedExchanges[0]);
    }
  };
  
  const handleEnabledChange = (e) => {
    setFormData(prev => ({
      ...prev,
      enabled: e.target.checked
    }));
  };
  
  const validateForm = () => {
    if (!formData.name.trim()) {
      showAlert('error', 'Name is required');
      return false;
    }
    
    if (!formData.condition) {
      showAlert('error', 'Condition is required');
      return false;
    }
    
    if (!formData.action) {
      showAlert('error', 'Action is required');
      return false;
    }
    
    // Validate threshold values based on condition type
    const threshold = formData.parameters.threshold;
    if (threshold === undefined || isNaN(threshold)) {
      showAlert('error', 'Threshold must be a number');
      return false;
    }
    
    return true;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      if (editMode) {
        await api.put(`/risk/circuit-breakers/${formData.id}`, formData);
        showAlert('success', 'Circuit breaker updated successfully');
        if (onBreakerUpdated) onBreakerUpdated(formData);
      } else {
        const response = await api.post('/risk/circuit-breakers', formData);
        showAlert('success', 'Circuit breaker created successfully');
        if (onBreakerCreated) onBreakerCreated(response.data);
      }
      
      // Refresh the list of circuit breakers
      fetchCircuitBreakers();
      
      // Reset the form
      setFormData({ ...DEFAULT_CIRCUIT_BREAKER });
      setEditMode(false);
    } catch (error) {
      showAlert('error', `Failed to ${editMode ? 'update' : 'create'} circuit breaker`);
      console.error(`Error ${editMode ? 'updating' : 'creating'} circuit breaker:`, error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleEdit = (breaker) => {
    setFormData(breaker);
    setEditMode(true);
  };
  
  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this circuit breaker?')) {
      return;
    }
    
    setLoading(true);
    try {
      await api.delete(`/risk/circuit-breakers/${id}`);
      showAlert('success', 'Circuit breaker deleted successfully');
      if (onBreakerDeleted) onBreakerDeleted(id);
      
      // Refresh the list of circuit breakers
      fetchCircuitBreakers();
    } catch (error) {
      showAlert('error', 'Failed to delete circuit breaker');
      console.error('Error deleting circuit breaker:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleReset = () => {
    setFormData({ ...DEFAULT_CIRCUIT_BREAKER });
    setEditMode(false);
  };
  
  return (
    <Box>
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
      
      <Box mb={4}>
        <Card>
          <CardHeader
            title={editMode ? "Edit Circuit Breaker" : "Create Circuit Breaker"}
            subheader="Configure automated risk management rules"
          />
          <Divider />
          <CardContent>
            <form onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    fullWidth
                    required
                    helperText="A descriptive name for this circuit breaker"
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.enabled}
                        onChange={handleEnabledChange}
                        color="primary"
                      />
                    }
                    label="Enabled"
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    label="Description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    fullWidth
                    multiline
                    rows={2}
                    helperText="Optional description of when this circuit breaker will trigger"
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Condition</InputLabel>
                    <Select
                      name="condition"
                      value={formData.condition}
                      onChange={handleConditionChange}
                      label="Condition"
                    >
                      {CONDITION_TYPES.map(condition => (
                        <MenuItem key={condition.value} value={condition.value}>
                          {condition.label}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {CONDITION_TYPES.find(c => c.value === formData.condition)?.description}
                    </FormHelperText>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Action</InputLabel>
                    <Select
                      name="action"
                      value={formData.action}
                      onChange={handleActionChange}
                      label="Action"
                    >
                      {ACTION_TYPES.map(action => (
                        <MenuItem key={action.value} value={action.value}>
                          {action.label}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {ACTION_TYPES.find(a => a.value === formData.action)?.description}
                    </FormHelperText>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Threshold"
                    name="threshold"
                    type="number"
                    value={formData.parameters.threshold}
                    onChange={handleParameterChange}
                    fullWidth
                    InputProps={{
                      endAdornment: <Typography variant="caption">%</Typography>
                    }}
                    helperText={`Trigger when ${formData.condition.replace('_', ' ')} exceeds this value`}
                  />
                </Grid>
                
                {formData.action === 'reduce_position' && (
                  <Grid item xs={12} md={6}>
                    <TextField
                      label="Reduction Percentage"
                      name="reduction_percentage"
                      type="number"
                      value={formData.parameters.reduction_percentage || 50}
                      onChange={handleParameterChange}
                      fullWidth
                      InputProps={{
                        endAdornment: <Typography variant="caption">%</Typography>
                      }}
                      helperText="Percentage of the position to reduce"
                    />
                  </Grid>
                )}
                
                {formData.action === 'close_position' && (
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          name="close_all"
                          checked={formData.parameters.close_all || false}
                          onChange={handleParameterChange}
                        />
                      }
                      label="Close all positions"
                    />
                    <FormHelperText>
                      If checked, all positions will be closed. Otherwise, only the largest position will be closed.
                    </FormHelperText>
                  </Grid>
                )}
                
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Exchanges (Optional)</InputLabel>
                    <Select
                      name="exchanges"
                      multiple
                      value={formData.exchanges}
                      onChange={handleExchangesChange}
                      label="Exchanges (Optional)"
                      native
                    >
                      {exchangeList.map(exchange => (
                        <option key={exchange.id} value={exchange.id}>
                          {exchange.name}
                        </option>
                      ))}
                    </Select>
                    <FormHelperText>
                      Select exchanges to limit this breaker to (leave empty for all exchanges)
                    </FormHelperText>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Symbols (Optional)</InputLabel>
                    <Select
                      name="symbols"
                      multiple
                      value={formData.symbols}
                      onChange={handleSymbolsChange}
                      label="Symbols (Optional)"
                      native
                      disabled={formData.exchanges.length !== 1}
                    >
                      {symbolList.map(symbol => (
                        <option key={symbol} value={symbol}>
                          {symbol}
                        </option>
                      ))}
                    </Select>
                    <FormHelperText>
                      {formData.exchanges.length !== 1 
                        ? "Select exactly one exchange to choose symbols" 
                        : "Select symbols to limit this breaker to (leave empty for all symbols)"}
                    </FormHelperText>
                  </FormControl>
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
                      startIcon={editMode ? <SaveIcon /> : <AddIcon />}
                      disabled={loading}
                    >
                      {loading ? (
                        <CircularProgress size={24} />
                      ) : editMode ? (
                        "Update Circuit Breaker"
                      ) : (
                        "Create Circuit Breaker"
                      )}
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </form>
          </CardContent>
        </Card>
      </Box>
      
      <Box>
        <Typography variant="h6" gutterBottom>
          Configured Circuit Breakers
        </Typography>
        
        {loading && <CircularProgress />}
        
        {!loading && circuitBreakers.length === 0 && (
          <Alert severity="info">No circuit breakers configured yet</Alert>
        )}
        
        {!loading && circuitBreakers.map(breaker => (
          <Card key={breaker.id} sx={{ mb: 2 }}>
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="center">
                    <Typography variant="h6" component="div">
                      {breaker.name}
                    </Typography>
                    <Box ml={1}>
                      <Chip 
                        size="small"
                        label={breaker.enabled ? "Enabled" : "Disabled"}
                        color={breaker.enabled ? "success" : "default"}
                      />
                    </Box>
                  </Box>
                  <Typography variant="body2" color="textSecondary">
                    {breaker.description}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2">
                    <strong>Condition:</strong> {CONDITION_TYPES.find(c => c.value === breaker.condition)?.label || breaker.condition}
                    {breaker.parameters.threshold && ` (${breaker.parameters.threshold}%)`}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Action:</strong> {ACTION_TYPES.find(a => a.value === breaker.action)?.label || breaker.action}
                  </Typography>
                  {breaker.last_triggered_at && (
                    <Typography variant="body2" color="warning.main">
                      <WarningIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                      Last triggered: {formatDateTime(breaker.last_triggered_at)}
                    </Typography>
                  )}
                </Grid>
                
                <Grid item xs={12} sm={2}>
                  <Box display="flex" justifyContent="flex-end">
                    <IconButton
                      color="primary"
                      onClick={() => handleEdit(breaker)}
                      disabled={loading}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      color="error"
                      onClick={() => handleDelete(breaker.id)}
                      disabled={loading}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
};

export default CircuitBreakerForm; 