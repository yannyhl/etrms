import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  CardActions,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  CircularProgress,
  Alert,
  Divider,
  Rating,
  IconButton,
  Tooltip
} from '@mui/material';
import { 
  TrendingUp, 
  TrendingDown, 
  SwapHoriz, 
  FlashOn, 
  ShowChart,
  Info,
  Visibility,
  ArrowForward
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';

const SetupDetection = ({ exchanges, symbols }) => {
  const [selectedExchange, setSelectedExchange] = useState('');
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [minQuality, setMinQuality] = useState(0.6);
  const [setups, setSetups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const { get } = useApi();
  
  const timeframes = ['5m', '15m', '30m', '1h', '4h', '1d'];
  
  useEffect(() => {
    // Auto-select first exchange and symbol if available
    if (exchanges.length > 0 && !selectedExchange) {
      setSelectedExchange(exchanges[0].id);
    }
    
    if (symbols.length > 0 && !selectedSymbol) {
      setSelectedSymbol(symbols[0].id);
    }
  }, [exchanges, symbols, selectedExchange, selectedSymbol]);
  
  const fetchSetups = async () => {
    if (!selectedExchange || !selectedSymbol) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        exchange: selectedExchange,
        symbol: selectedSymbol,
        timeframe: selectedTimeframe,
        min_quality: minQuality
      };
      
      const response = await get('/api/v1/assistant/setups', { params });
      setSetups(response.data || []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching setups:', err);
      setError('Failed to load trading setups. Please try again.');
      setLoading(false);
    }
  };
  
  useEffect(() => {
    if (selectedExchange && selectedSymbol && selectedTimeframe) {
      fetchSetups();
    }
  }, [selectedExchange, selectedSymbol, selectedTimeframe]);
  
  const getSetupIcon = (setupType) => {
    switch (setupType) {
      case 'trend_continuation':
        return <TrendingUp />;
      case 'trend_reversal':
        return <TrendingDown />;
      case 'breakout':
        return <FlashOn />;
      case 'range_bounce':
        return <SwapHoriz />;
      default:
        return <ShowChart />;
    }
  };
  
  const getSetupColor = (setupType) => {
    switch (setupType) {
      case 'trend_continuation':
        return 'success';
      case 'trend_reversal':
        return 'warning';
      case 'breakout':
        return 'primary';
      case 'range_bounce':
        return 'secondary';
      default:
        return 'default';
    }
  };
  
  const formatSetupType = (setupType) => {
    return setupType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  const handleRefresh = () => {
    fetchSetups();
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Trading Setup Detection
      </Typography>
      <Typography variant="body2" color="textSecondary" paragraph>
        Automatically detect potential trading setups based on technical analysis and pattern recognition.
      </Typography>
      
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth>
            <InputLabel id="exchange-select-label">Exchange</InputLabel>
            <Select
              labelId="exchange-select-label"
              value={selectedExchange}
              label="Exchange"
              onChange={(e) => setSelectedExchange(e.target.value)}
            >
              {exchanges.map((exchange) => (
                <MenuItem key={exchange.id} value={exchange.id}>
                  {exchange.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth>
            <InputLabel id="symbol-select-label">Symbol</InputLabel>
            <Select
              labelId="symbol-select-label"
              value={selectedSymbol}
              label="Symbol"
              onChange={(e) => setSelectedSymbol(e.target.value)}
            >
              {symbols.map((symbol) => (
                <MenuItem key={symbol.id} value={symbol.id}>
                  {symbol.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth>
            <InputLabel id="timeframe-select-label">Timeframe</InputLabel>
            <Select
              labelId="timeframe-select-label"
              value={selectedTimeframe}
              label="Timeframe"
              onChange={(e) => setSelectedTimeframe(e.target.value)}
            >
              {timeframes.map((timeframe) => (
                <MenuItem key={timeframe} value={timeframe}>
                  {timeframe}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth>
            <TextField
              label="Min Quality"
              type="number"
              value={minQuality}
              onChange={(e) => setMinQuality(parseFloat(e.target.value))}
              inputProps={{ min: 0, max: 1, step: 0.1 }}
            />
          </FormControl>
        </Grid>
      </Grid>
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button 
          variant="contained" 
          onClick={handleRefresh}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Loading...' : 'Refresh Setups'}
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : setups.length === 0 ? (
        <Alert severity="info">
          No trading setups detected for the selected criteria. Try changing the symbol, timeframe, or lowering the minimum quality threshold.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {setups.map((setup) => (
            <Grid item xs={12} sm={6} md={4} key={setup.id}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Chip 
                      icon={getSetupIcon(setup.type)} 
                      label={formatSetupType(setup.type)} 
                      color={getSetupColor(setup.type)}
                      size="small"
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body2" color="textSecondary" sx={{ mr: 1 }}>
                        Quality:
                      </Typography>
                      <Rating 
                        value={setup.quality * 5} 
                        precision={0.5} 
                        readOnly 
                        size="small"
                      />
                    </Box>
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Symbol:</strong> {setup.symbol}
                  </Typography>
                  
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Exchange:</strong> {setup.exchange}
                  </Typography>
                  
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Timeframe:</strong> {setup.timeframe}
                  </Typography>
                  
                  {setup.market_regime && (
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Market Regime:</strong> {setup.market_regime}
                    </Typography>
                  )}
                  
                  <Typography variant="body2" color="textSecondary" sx={{ fontSize: '0.75rem' }}>
                    Detected: {new Date(setup.detection_time).toLocaleString()}
                  </Typography>
                </CardContent>
                <Divider />
                <CardActions>
                  <Button 
                    size="small" 
                    startIcon={<Visibility />}
                    href={`/chart?symbol=${setup.symbol}&exchange=${setup.exchange}&timeframe=${setup.timeframe}`}
                  >
                    View Chart
                  </Button>
                  <Button 
                    size="small" 
                    color="primary" 
                    endIcon={<ArrowForward />}
                    href={`/ai-assistant?tab=1&setupId=${setup.id}`}
                  >
                    Get Recommendations
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default SetupDetection; 