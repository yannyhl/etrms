import React, { useState } from 'react';
import { 
  Card, CardHeader, CardContent, 
  Grid, TextField, Button, 
  Typography, Alert, FormHelperText,
  InputAdornment, CircularProgress
} from '@mui/material';
import axios from 'axios';
import { API_BASE_URL } from '../../config';

/**
 * MonteCarloForm component for configuring and running Monte Carlo simulations
 * on existing backtest results.
 * 
 * @param {Object} props - Component props
 * @param {string} props.taskId - The ID of the backtest task to analyze
 * @param {function} props.onSimulationComplete - Callback when simulation completes
 */
function MonteCarloForm({ taskId, onSimulationComplete }) {
  // Form state
  const [formValues, setFormValues] = useState({
    simulations: 1000,
    random_seed: ''
  });
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  // Form validation
  const [formErrors, setFormErrors] = useState({});
  
  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    let processedValue = value;
    
    // Convert numeric fields to numbers
    if (name === 'simulations' || name === 'random_seed') {
      processedValue = value === '' ? '' : Number(value);
    }
    
    setFormValues({
      ...formValues,
      [name]: processedValue
    });
    
    // Clear error when field is modified
    if (formErrors[name]) {
      setFormErrors({
        ...formErrors,
        [name]: null
      });
    }
  };
  
  // Validate form before submission
  const validateForm = () => {
    const errors = {};
    const { simulations, random_seed } = formValues;
    
    if (!simulations || simulations < 100) {
      errors.simulations = 'At least 100 simulations are required for meaningful results';
    } else if (simulations > 10000) {
      errors.simulations = 'Maximum 10,000 simulations allowed for performance reasons';
    }
    
    if (random_seed !== '' && (random_seed < 0 || !Number.isInteger(random_seed))) {
      errors.random_seed = 'Random seed must be a positive integer or leave empty for random seed';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Reset status
    setError(null);
    setSuccess(false);
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    // Create submission data
    const submissionData = {
      simulations: formValues.simulations
    };
    
    // Only include random_seed if provided
    if (formValues.random_seed !== '') {
      submissionData.random_seed = formValues.random_seed;
    }
    
    setIsLoading(true);
    
    try {
      const response = await axios.post(
        `${API_BASE_URL}/backtest/monte-carlo/${taskId}`,
        submissionData
      );
      
      setSuccess(true);
      setIsLoading(false);
      
      // Call the callback with the simulation ID or results
      if (onSimulationComplete) {
        onSimulationComplete(response.data);
      }
    } catch (err) {
      setIsLoading(false);
      
      if (err.response && err.response.data) {
        setError(err.response.data.message || 'Failed to run Monte Carlo simulation');
      } else {
        setError('Network error or server unreachable');
      }
    }
  };
  
  // Reset the form
  const handleReset = () => {
    setFormValues({
      simulations: 1000,
      random_seed: ''
    });
    setFormErrors({});
    setError(null);
    setSuccess(false);
  };
  
  return (
    <Card variant="outlined">
      <CardHeader 
        title="Monte Carlo Simulation" 
        subheader="Analyze the distribution of possible outcomes by randomizing trade order"
      />
      <CardContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Monte Carlo simulation started successfully! Results will be available shortly.
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="body2" color="textSecondary" paragraph>
                Monte Carlo simulation randomizes the order of trades from your backtest to 
                analyze how sequence affects results. This helps understand the robustness
                of your strategy and the range of possible outcomes.
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Number of Simulations"
                name="simulations"
                type="number"
                value={formValues.simulations}
                onChange={handleChange}
                error={!!formErrors.simulations}
                helperText={formErrors.simulations || "More simulations provide more statistically significant results"}
                InputProps={{
                  endAdornment: <InputAdornment position="end">runs</InputAdornment>,
                }}
                inputProps={{ min: 100, max: 10000 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Random Seed (Optional)"
                name="random_seed"
                type="number"
                value={formValues.random_seed}
                onChange={handleChange}
                error={!!formErrors.random_seed}
                helperText={formErrors.random_seed || "Leave empty for random seed, or set for reproducible results"}
                inputProps={{ min: 0 }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormHelperText>
                Processing time depends on the number of trades and simulations. Large simulations may take several minutes.
              </FormHelperText>
            </Grid>
            
            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={isLoading}
                sx={{ mr: 2 }}
              >
                {isLoading ? <CircularProgress size={24} /> : 'Run Simulation'}
              </Button>
              <Button
                type="button"
                variant="outlined"
                onClick={handleReset}
                disabled={isLoading}
              >
                Reset
              </Button>
            </Grid>
          </Grid>
        </form>
      </CardContent>
    </Card>
  );
}

export default MonteCarloForm; 