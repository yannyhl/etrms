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
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { 
  Warning,
  CheckCircle,
  Error,
  Info,
  ExpandMore,
  Assessment,
  TrendingUp,
  Psychology,
  ShowChart,
  CalendarToday,
  Category
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`performance-analysis-tabpanel-${index}`}
      aria-labelledby={`performance-analysis-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 2 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index) {
  return {
    id: `performance-analysis-tab-${index}`,
    'aria-controls': `performance-analysis-tabpanel-${index}`,
  };
}

const PerformanceAnalysis = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  
  const { post } = useApi();
  
  // Sample trade data for demonstration
  const sampleTrades = [
    {
      id: 'trade_20230501123456',
      symbol: 'BTCUSDT',
      exchange: 'binance',
      direction: 'long',
      entry_price: 40000,
      exit_price: 42000,
      entry_time: '2023-05-01T12:34:56Z',
      exit_time: '2023-05-02T09:45:23Z',
      position_size: 0.5,
      profit_loss: 1000,
      profit_loss_percent: 5.0,
      setup_type: 'breakout',
      market_regime: 'trending'
    },
    {
      id: 'trade_20230503145623',
      symbol: 'ETHUSDT',
      exchange: 'binance',
      direction: 'long',
      entry_price: 2800,
      exit_price: 2750,
      entry_time: '2023-05-03T14:56:23Z',
      exit_time: '2023-05-04T10:12:45Z',
      position_size: 2.0,
      profit_loss: -100,
      profit_loss_percent: -1.79,
      setup_type: 'trend_continuation',
      market_regime: 'ranging'
    },
    {
      id: 'trade_20230505092345',
      symbol: 'SOLUSDT',
      exchange: 'binance',
      direction: 'short',
      entry_price: 95,
      exit_price: 88,
      entry_time: '2023-05-05T09:23:45Z',
      exit_time: '2023-05-06T15:34:12Z',
      position_size: 10.0,
      profit_loss: 70,
      profit_loss_percent: 7.37,
      setup_type: 'trend_reversal',
      market_regime: 'volatile'
    },
    {
      id: 'trade_20230508103421',
      symbol: 'BTCUSDT',
      exchange: 'hyperliquid',
      direction: 'long',
      entry_price: 39500,
      exit_price: 41200,
      entry_time: '2023-05-08T10:34:21Z',
      exit_time: '2023-05-09T08:23:45Z',
      position_size: 0.3,
      profit_loss: 510,
      profit_loss_percent: 4.3,
      setup_type: 'breakout',
      market_regime: 'trending'
    },
    {
      id: 'trade_20230510143256',
      symbol: 'ETHUSDT',
      exchange: 'hyperliquid',
      direction: 'short',
      entry_price: 2900,
      exit_price: 2950,
      entry_time: '2023-05-10T14:32:56Z',
      exit_time: '2023-05-11T11:45:23Z',
      position_size: 1.5,
      profit_loss: -75,
      profit_loss_percent: -1.72,
      setup_type: 'range_bounce',
      market_regime: 'ranging'
    }
  ];
  
  // Sample market regime data for demonstration
  const sampleMarketRegimes = {
    'BTCUSDT': [
      { timestamp: '2023-05-01T00:00:00Z', regime: 'trending', volatility: 'normal' },
      { timestamp: '2023-05-05T00:00:00Z', regime: 'volatile', volatility: 'high' },
      { timestamp: '2023-05-08T00:00:00Z', regime: 'trending', volatility: 'normal' }
    ],
    'ETHUSDT': [
      { timestamp: '2023-05-01T00:00:00Z', regime: 'ranging', volatility: 'low' },
      { timestamp: '2023-05-06T00:00:00Z', regime: 'trending', volatility: 'normal' },
      { timestamp: '2023-05-10T00:00:00Z', regime: 'ranging', volatility: 'normal' }
    ],
    'SOLUSDT': [
      { timestamp: '2023-05-01T00:00:00Z', regime: 'volatile', volatility: 'high' },
      { timestamp: '2023-05-07T00:00:00Z', regime: 'trending', volatility: 'normal' }
    ]
  };
  
  const analyzePerformance = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // In a real implementation, this would call the API
      // For now, we'll simulate a response
      setTimeout(() => {
        // Simulate API response
        const analysis = {
          status: 'success',
          trade_count: sampleTrades.length,
          overall_metrics: {
            win_rate: 0.6,
            profit_factor: 2.1,
            average_win: 5.56,
            average_loss: 1.76,
            risk_reward: 3.16,
            max_drawdown: 3.51,
            sharpe_ratio: 1.8,
            sortino_ratio: 2.3,
            expectancy: 1.05,
            profit_per_day: 0.8
          },
          biases: {
            loss_aversion: 0.7,
            disposition_effect: 0.6
          },
          regime_performance: {
            trending: {
              win_rate: 1.0,
              profit_factor: 3.5,
              average_win: 4.65,
              average_loss: 0,
              trade_count: 2
            },
            ranging: {
              win_rate: 0,
              profit_factor: 0,
              average_win: 0,
              average_loss: 1.76,
              trade_count: 2
            },
            volatile: {
              win_rate: 1.0,
              profit_factor: 3.0,
              average_win: 7.37,
              average_loss: 0,
              trade_count: 1
            }
          },
          time_performance: {
            daily: {
              monday: { win_rate: 0.5, profit_factor: 1.2, trade_count: 2 },
              wednesday: { win_rate: 1.0, profit_factor: 3.0, trade_count: 1 },
              friday: { win_rate: 0.5, profit_factor: 2.0, trade_count: 2 }
            }
          },
          setup_performance: {
            breakout: {
              win_rate: 1.0,
              profit_factor: 3.0,
              average_win: 4.65,
              average_loss: 0,
              trade_count: 2
            },
            trend_continuation: {
              win_rate: 0,
              profit_factor: 0,
              average_win: 0,
              average_loss: 1.79,
              trade_count: 1
            },
            trend_reversal: {
              win_rate: 1.0,
              profit_factor: 3.0,
              average_win: 7.37,
              average_loss: 0,
              trade_count: 1
            },
            range_bounce: {
              win_rate: 0,
              profit_factor: 0,
              average_win: 0,
              average_loss: 1.72,
              trade_count: 1
            }
          },
          suggestions: [
            {
              category: 'bias',
              type: 'loss_aversion',
              title: 'Loss Aversion Detected',
              description: 'You tend to cut winners too early and let losers run too long.',
              action: 'Consider using automated take profit and stop loss orders to remove emotion from exits.',
              score: 0.7,
              priority: 'medium'
            },
            {
              category: 'bias',
              type: 'disposition_effect',
              title: 'Disposition Effect Detected',
              description: 'You tend to sell winners too early and hold losers too long.',
              action: 'Implement a rule-based exit strategy and stick to it regardless of emotions.',
              score: 0.6,
              priority: 'medium'
            },
            {
              category: 'regime',
              type: 'regime_optimization',
              title: 'Optimize for Trending Markets',
              description: 'Your performance is significantly better in trending markets.',
              action: 'Consider increasing position size during trending market conditions.',
              priority: 'medium'
            },
            {
              category: 'regime',
              type: 'regime_caution',
              title: 'Caution in Ranging Markets',
              description: 'Your performance is weaker in ranging markets.',
              action: 'Consider reducing position size or avoiding trading during ranging market conditions.',
              priority: 'high'
            },
            {
              category: 'setup',
              type: 'setup_focus',
              title: 'Focus on Breakout Setups',
              description: 'Your performance is significantly better with breakout setups.',
              action: 'Consider focusing more on breakout setups and increasing position size for these trades.',
              priority: 'medium'
            }
          ],
          charts: {}
        };
        
        setPerformanceData(analysis);
        setLoading(false);
      }, 1500);
      
    } catch (err) {
      console.error('Error analyzing performance:', err);
      setError('Failed to analyze performance. Please try again.');
      setLoading(false);
    }
  };
  
  useEffect(() => {
    // Auto-analyze on component mount
    analyzePerformance();
  }, []);
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };
  
  const formatMetricValue = (metric, value) => {
    if (metric.includes('rate') || metric.includes('drawdown')) {
      return `${(value * 100).toFixed(2)}%`;
    } else if (metric.includes('factor') || metric.includes('ratio')) {
      return value.toFixed(2);
    } else if (metric.includes('average')) {
      return `${value.toFixed(2)}%`;
    } else {
      return value.toFixed(2);
    }
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Performance Analysis
      </Typography>
      <Typography variant="body2" color="textSecondary" paragraph>
        Analyze your trading performance to identify strengths, weaknesses, and improvement opportunities.
      </Typography>
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button 
          variant="contained" 
          onClick={analyzePerformance}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Analyzing...' : 'Refresh Analysis'}
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}
      
      {loading && !performanceData ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : !performanceData ? (
        <Alert severity="info">
          No performance data available. Click "Analyze Performance" to generate an analysis.
        </Alert>
      ) : (
        <Box>
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange} 
              aria-label="Performance analysis tabs"
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab icon={<Assessment />} label="Overview" {...a11yProps(0)} />
              <Tab icon={<Psychology />} label="Biases" {...a11yProps(1)} />
              <Tab icon={<ShowChart />} label="By Market Regime" {...a11yProps(2)} />
              <Tab icon={<Category />} label="By Setup Type" {...a11yProps(3)} />
              <Tab icon={<CalendarToday />} label="By Time Period" {...a11yProps(4)} />
              <Tab icon={<Info />} label="Suggestions" {...a11yProps(5)} />
            </Tabs>
          </Box>
          
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Overall Performance Metrics
                    </Typography>
                    
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Metric</TableCell>
                            <TableCell align="right">Value</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {Object.entries(performanceData.overall_metrics).map(([metric, value]) => (
                            <TableRow key={metric}>
                              <TableCell>
                                {metric.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                              </TableCell>
                              <TableCell align="right">{formatMetricValue(metric, value)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Trade Summary
                    </Typography>
                    
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Symbol</TableCell>
                            <TableCell>Direction</TableCell>
                            <TableCell>Entry</TableCell>
                            <TableCell>Exit</TableCell>
                            <TableCell align="right">P/L %</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {sampleTrades.map((trade) => (
                            <TableRow key={trade.id}>
                              <TableCell>{trade.symbol}</TableCell>
                              <TableCell>{trade.direction}</TableCell>
                              <TableCell>{trade.entry_price}</TableCell>
                              <TableCell>{trade.exit_price}</TableCell>
                              <TableCell 
                                align="right"
                                sx={{ 
                                  color: trade.profit_loss_percent >= 0 ? 'success.main' : 'error.main'
                                }}
                              >
                                {trade.profit_loss_percent >= 0 ? '+' : ''}{trade.profit_loss_percent.toFixed(2)}%
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Top Improvement Suggestions
                    </Typography>
                    
                    <List>
                      {performanceData.suggestions.slice(0, 3).map((suggestion, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <Info color="info" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Typography variant="body1">
                                  {suggestion.title}
                                </Typography>
                                <Chip 
                                  label={suggestion.priority} 
                                  size="small" 
                                  color={getPriorityColor(suggestion.priority)}
                                  sx={{ ml: 1 }}
                                />
                              </Box>
                            }
                            secondary={
                              <>
                                <Typography variant="body2" color="textSecondary">
                                  {suggestion.description}
                                </Typography>
                                <Typography variant="body2" color="primary" sx={{ mt: 0.5 }}>
                                  <strong>Action:</strong> {suggestion.action}
                                </Typography>
                              </>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                  <CardActions>
                    <Button 
                      size="small" 
                      onClick={() => setTabValue(5)}
                    >
                      View All Suggestions
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              {Object.entries(performanceData.biases).map(([bias, score]) => (
                <Grid item xs={12} key={bias}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">
                          {bias.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                        </Typography>
                        <Chip 
                          label={`Score: ${(score * 100).toFixed(0)}%`} 
                          color={score > 0.7 ? 'error' : score > 0.5 ? 'warning' : 'info'}
                        />
                      </Box>
                      
                      <Typography variant="body1" paragraph>
                        {bias === 'loss_aversion' ? (
                          'The tendency to prefer avoiding losses over acquiring equivalent gains. This causes traders to cut winners too early and let losers run too long.'
                        ) : bias === 'disposition_effect' ? (
                          'The tendency to sell assets that have increased in value and hold assets that have decreased in value. This results in selling winners too early and holding losers too long.'
                        ) : (
                          'A cognitive bias affecting trading decisions.'
                        )}
                      </Typography>
                      
                      <Typography variant="subtitle2" gutterBottom>
                        Mitigation Strategies:
                      </Typography>
                      
                      <List dense>
                        {bias === 'loss_aversion' ? (
                          <>
                            <ListItem>
                              <ListItemIcon>
                                <CheckCircle fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary="Use predetermined take profit and stop loss levels" />
                            </ListItem>
                            <ListItem>
                              <ListItemIcon>
                                <CheckCircle fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary="Implement a mechanical trading system" />
                            </ListItem>
                            <ListItem>
                              <ListItemIcon>
                                <CheckCircle fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary="Keep a trading journal to track emotional decisions" />
                            </ListItem>
                          </>
                        ) : bias === 'disposition_effect' ? (
                          <>
                            <ListItem>
                              <ListItemIcon>
                                <CheckCircle fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary="Use trailing stops for winning trades" />
                            </ListItem>
                            <ListItem>
                              <ListItemIcon>
                                <CheckCircle fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary="Implement strict stop loss rules" />
                            </ListItem>
                            <ListItem>
                              <ListItemIcon>
                                <CheckCircle fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary="Evaluate positions based on future potential, not past performance" />
                            </ListItem>
                          </>
                        ) : (
                          <ListItem>
                            <ListItemIcon>
                              <CheckCircle fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary="Implement structured trading rules to mitigate this bias" />
                          </ListItem>
                        )}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </TabPanel>
          
          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              {Object.entries(performanceData.regime_performance).map(([regime, metrics]) => (
                <Grid item xs={12} md={4} key={regime}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {regime.charAt(0).toUpperCase() + regime.slice(1)} Markets
                      </Typography>
                      
                      <Typography variant="body2" color="textSecondary" paragraph>
                        {metrics.trade_count} trades
                      </Typography>
                      
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableBody>
                            <TableRow>
                              <TableCell>Win Rate</TableCell>
                              <TableCell align="right">{(metrics.win_rate * 100).toFixed(2)}%</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Profit Factor</TableCell>
                              <TableCell align="right">{metrics.profit_factor.toFixed(2)}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Average Win</TableCell>
                              <TableCell align="right">{metrics.average_win.toFixed(2)}%</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Average Loss</TableCell>
                              <TableCell align="right">{metrics.average_loss.toFixed(2)}%</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </TabPanel>
          
          <TabPanel value={tabValue} index={3}>
            <Grid container spacing={3}>
              {Object.entries(performanceData.setup_performance).map(([setup, metrics]) => (
                <Grid item xs={12} md={6} key={setup}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {setup.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                      </Typography>
                      
                      <Typography variant="body2" color="textSecondary" paragraph>
                        {metrics.trade_count} trades
                      </Typography>
                      
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableBody>
                            <TableRow>
                              <TableCell>Win Rate</TableCell>
                              <TableCell align="right">{(metrics.win_rate * 100).toFixed(2)}%</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Profit Factor</TableCell>
                              <TableCell align="right">{metrics.profit_factor.toFixed(2)}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Average Win</TableCell>
                              <TableCell align="right">{metrics.average_win.toFixed(2)}%</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Average Loss</TableCell>
                              <TableCell align="right">{metrics.average_loss.toFixed(2)}%</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </TabPanel>
          
          <TabPanel value={tabValue} index={4}>
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="subtitle1">Performance by Day of Week</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Day</TableCell>
                        <TableCell align="right">Win Rate</TableCell>
                        <TableCell align="right">Profit Factor</TableCell>
                        <TableCell align="right">Trade Count</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(performanceData.time_performance.daily).map(([day, metrics]) => (
                        <TableRow key={day}>
                          <TableCell>{day.charAt(0).toUpperCase() + day.slice(1)}</TableCell>
                          <TableCell align="right">{(metrics.win_rate * 100).toFixed(2)}%</TableCell>
                          <TableCell align="right">{metrics.profit_factor.toFixed(2)}</TableCell>
                          <TableCell align="right">{metrics.trade_count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          </TabPanel>
          
          <TabPanel value={tabValue} index={5}>
            <Grid container spacing={2}>
              {performanceData.suggestions.map((suggestion, index) => (
                <Grid item xs={12} key={index}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle1">
                          {suggestion.title}
                        </Typography>
                        <Chip 
                          label={suggestion.priority} 
                          color={getPriorityColor(suggestion.priority)}
                          size="small"
                        />
                      </Box>
                      
                      <Typography variant="body2" paragraph>
                        {suggestion.description}
                      </Typography>
                      
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        Recommended Action:
                      </Typography>
                      <Typography variant="body2" paragraph>
                        {suggestion.action}
                      </Typography>
                      
                      {suggestion.score && (
                        <Typography variant="body2" color="textSecondary">
                          Detection Score: {(suggestion.score * 100).toFixed(0)}%
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </TabPanel>
        </Box>
      )}
    </Box>
  );
};

export default PerformanceAnalysis; 