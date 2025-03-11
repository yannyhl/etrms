import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  CircularProgress
} from '@mui/material';
import { EXCHANGES, TIMEFRAMES } from '../../config';

const BasicBacktestForm = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    name: '',
    exchange: '',
    symbol: '',
    timeframe: '',
    startDate: '',
    endDate: '',
    initialCapital: 10000,
    leverage: 1
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Basic Backtest Configuration
        </Typography>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Backtest Name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel id="exchange-label">Exchange</InputLabel>
                <Select
                  labelId="exchange-label"
                  name="exchange"
                  value={formData.exchange}
                  onChange={handleChange}
                  label="Exchange"
                >
                  {EXCHANGES.map(exchange => (
                    <MenuItem key={exchange.value} value={exchange.value}>
                      {exchange.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Symbol"
                name="symbol"
                value={formData.symbol}
                onChange={handleChange}
                required
                placeholder="e.g. BTCUSDT"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth required>
                <InputLabel id="timeframe-label">Timeframe</InputLabel>
                <Select
                  labelId="timeframe-label"
                  name="timeframe"
                  value={formData.timeframe}
                  onChange={handleChange}
                  label="Timeframe"
                >
                  {TIMEFRAMES.map(timeframe => (
                    <MenuItem key={timeframe.value} value={timeframe.value}>
                      {timeframe.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Start Date"
                name="startDate"
                type="date"
                value={formData.startDate}
                onChange={handleChange}
                required
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="End Date"
                name="endDate"
                type="date"
                value={formData.endDate}
                onChange={handleChange}
                required
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Initial Capital"
                name="initialCapital"
                type="number"
                value={formData.initialCapital}
                onChange={handleChange}
                required
                InputProps={{
                  startAdornment: '$',
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Leverage"
                name="leverage"
                type="number"
                value={formData.leverage}
                onChange={handleChange}
                required
                inputProps={{
                  min: 1,
                  max: 100,
                  step: 1
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={loading}
                  startIcon={loading && <CircularProgress size={20} />}
                >
                  {loading ? 'Running Backtest...' : 'Run Backtest'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

export default BasicBacktestForm; 