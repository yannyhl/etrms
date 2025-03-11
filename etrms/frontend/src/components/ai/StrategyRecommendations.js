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
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { 
  TrendingUp, 
  TrendingDown, 
  SwapHoriz, 
  FlashOn, 
  ShowChart,
  Info,
  Warning,
  ExpandMore,
  ArrowForward,
  Assessment
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';
import { useLocation } from 'react-router-dom';

const StrategyRecommendations = ({ exchanges, symbols }) => {
  const [selectedExchange, setSelectedExchange] = useState('');
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [selectedTimeframe, setSelectedTimeframe] = useState('');
  const [selectedStrategyType, setSelectedStrategyType] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [setupId, setSetupId] = useState(null);
  
  const { get } = useApi();
  const location = useLocation();
  
  const timeframes = ['5m', '15m', '30m', '1h', '4h', '1d'];
  const strategyTypes = [
    { id: 'trend_following', name: 'Trend Following' },
    { id: 'mean_reversion', name: 'Mean Reversion' },
    { id: 'breakout', name: 'Breakout' },
    { id: 'momentum', name: 'Momentum' },
    { id: 'volatility', name: 'Volatility' },
    { id: 'pattern_based', name: 'Pattern Based' }
  ];
  
  useEffect(() => {
    // Auto-select first exchange and symbol if available
    if (exchanges.length > 0 && !selectedExchange) {
      setSelectedExchange(exchanges[0].id);
    }
    
    if (symbols.length > 0 && !selectedSymbol) {
      setSelectedSymbol(symbols[0].id);
    }
    
    if (!selectedTimeframe && timeframes.length > 0) {
      setSelectedTimeframe(timeframes[3]); // Default to 1h
    }
    
    // Check for setupId in URL query params
    const params = new URLSearchParams(location.search);
    const setupIdParam = params.get('setupId');
    if (setupIdParam) {
      setSetupId(setupIdParam);
    }
  }, [exchanges, symbols, location.search, selectedExchange, selectedSymbol, selectedTimeframe]);
  
  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      let params = {};
      
      // If we have a setupId, use that directly
      if (setupId) {
        // This would be a different endpoint in a real implementation
        // For now, we'll just use the regular endpoint with filters
        params = { setup_id: setupId };
      } else {
        // Otherwise use the filters
        if (selectedExchange) params.exchange = selectedExchange;
        if (selectedSymbol) params.symbol = selectedSymbol;
        if (selectedTimeframe) params.timeframe = selectedTimeframe;
        if (selectedStrategyType) params.strategy_type = selectedStrategyType;
      }
      
      const response = await get('/api/v1/assistant/recommendations', { params });
      setRecommendations(response.data || []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError('Failed to load strategy recommendations. Please try again.');
      setLoading(false);
    }
  };
  
  useEffect(() => {
    // If we have a setupId, fetch recommendations immediately
    if (setupId) {
      fetchRecommendations();
    }
    // Otherwise, only fetch if we have the minimum required filters
    else if (selectedExchange && selectedSymbol && selectedTimeframe) {
      fetchRecommendations();
    }
  }, [setupId, selectedExchange, selectedSymbol, selectedTimeframe, selectedStrategyType]);
  
  const getStrategyIcon = (strategyType) => {
    switch (strategyType) {
      case 'trend_following':
        return <TrendingUp />;
      case 'mean_reversion':
        return <SwapHoriz />;
      case 'breakout':
        return <FlashOn />;
      case 'momentum':
        return <TrendingUp />;
      case 'volatility':
        return <ShowChart />;
      case 'pattern_based':
        return <ShowChart />;
      default:
        return <ShowChart />;
    }
  };
  
  const getStrategyColor = (strategyType) => {
    switch (strategyType) {
      case 'trend_following':
        return 'success';
      case 'mean_reversion':
        return 'secondary';
      case 'breakout':
        return 'primary';
      case 'momentum':
        return 'info';
      case 'volatility':
        return 'warning';
      case 'pattern_based':
        return 'default';
      default:
        return 'default';
    }
  };
  
  const getPositionSizingColor = (positionSizing) => {
    switch (positionSizing) {
      case 'increased':
        return 'success';
      case 'normal':
        return 'primary';
      case 'reduced':
        return 'warning';
      case 'minimum':
        return 'error';
      case 'maximum':
        return 'error';
      case 'avoid':
        return 'error';
      default:
        return 'default';
    }
  };
  
  const formatStrategyType = (strategyType) => {
    return strategyType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  const handleRefresh = () => {
    fetchRecommendations();
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Strategy Recommendations
      </Typography>
      <Typography variant="body2" color="textSecondary" paragraph>
        Get optimal trading strategies based on detected setups and current market conditions.
      </Typography>
      
      {!setupId && (
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
              <InputLabel id="strategy-type-select-label">Strategy Type</InputLabel>
              <Select
                labelId="strategy-type-select-label"
                value={selectedStrategyType}
                label="Strategy Type"
                onChange={(e) => setSelectedStrategyType(e.target.value)}
              >
                <MenuItem value="">All Types</MenuItem>
                {strategyTypes.map((strategy) => (
                  <MenuItem key={strategy.id} value={strategy.id}>
                    {strategy.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      )}
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button 
          variant="contained" 
          onClick={handleRefresh}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Loading...' : 'Refresh Recommendations'}
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : recommendations.length === 0 ? (
        <Alert severity="info">
          No strategy recommendations found for the selected criteria. Try changing the filters or check if there are any detected setups.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {recommendations.map((recommendation) => (
            <Grid item xs={12} key={recommendation.id}>
              <Card variant="outlined">
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={4}>
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Chip 
                            icon={getStrategyIcon(recommendation.strategy_type)} 
                            label={formatStrategyType(recommendation.strategy_type)} 
                            color={getStrategyColor(recommendation.strategy_type)}
                            sx={{ mr: 1 }}
                          />
                          <Chip 
                            label={`Position: ${recommendation.position_sizing}`} 
                            color={getPositionSizingColor(recommendation.position_sizing)}
                            size="small"
                          />
                        </Box>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Symbol:</strong> {recommendation.symbol}
                        </Typography>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Exchange:</strong> {recommendation.exchange}
                        </Typography>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Timeframe:</strong> {recommendation.timeframe}
                        </Typography>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Risk %:</strong> {recommendation.risk_percent}%
                        </Typography>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Risk/Reward:</strong> {recommendation.risk_reward}
                        </Typography>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Order Type:</strong> {formatStrategyType(recommendation.order_type)}
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle2" gutterBottom>
                        Entry & Exit Levels
                      </Typography>
                      
                      <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Level</TableCell>
                              <TableCell align="right">Price</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            <TableRow>
                              <TableCell>Entry (Min)</TableCell>
                              <TableCell align="right">{recommendation.entry_zone.min}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Entry (Ideal)</TableCell>
                              <TableCell align="right">{recommendation.entry_zone.ideal}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Entry (Max)</TableCell>
                              <TableCell align="right">{recommendation.entry_zone.max}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Stop Loss</TableCell>
                              <TableCell align="right">{recommendation.stop_loss}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Take Profit</TableCell>
                              <TableCell align="right">{recommendation.take_profit}</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Grid>
                    
                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle2" gutterBottom>
                        Notes & Warnings
                      </Typography>
                      
                      <List dense>
                        {recommendation.notes.map((note, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <Info fontSize="small" color="info" />
                            </ListItemIcon>
                            <ListItemText primary={note} />
                          </ListItem>
                        ))}
                      </List>
                    </Grid>
                  </Grid>
                </CardContent>
                <Divider />
                <CardActions>
                  <Button 
                    size="small" 
                    startIcon={<Assessment />}
                    href={`/ai-assistant?tab=2&setupId=${recommendation.setup_id}&recommendationId=${recommendation.id}`}
                  >
                    Risk Assessment
                  </Button>
                  <Button 
                    size="small" 
                    color="primary" 
                    endIcon={<ArrowForward />}
                    href={`/trading?action=new-order&setupId=${recommendation.setup_id}&recommendationId=${recommendation.id}`}
                  >
                    Create Order
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

export default StrategyRecommendations; 