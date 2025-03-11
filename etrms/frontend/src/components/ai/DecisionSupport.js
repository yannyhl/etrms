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
  Tabs,
  Tab,
  LinearProgress,
  Checkbox,
  TextField,
  Stack
} from '@mui/material';
import { 
  Warning,
  CheckCircle,
  Error,
  Info,
  ExpandMore,
  Assessment,
  BarChart,
  CheckBox,
  CheckBoxOutlineBlank,
  ArrowUpward,
  ArrowDownward
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';
import { useLocation } from 'react-router-dom';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`decision-support-tabpanel-${index}`}
      aria-labelledby={`decision-support-tab-${index}`}
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
    id: `decision-support-tab-${index}`,
    'aria-controls': `decision-support-tabpanel-${index}`,
  };
}

const DecisionSupport = ({ exchanges, symbols }) => {
  const [tabValue, setTabValue] = useState(0);
  const [selectedExchange, setSelectedExchange] = useState('');
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [setupId, setSetupId] = useState(null);
  const [recommendationId, setRecommendationId] = useState(null);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [checklist, setChecklist] = useState([]);
  const [scenarios, setScenarios] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPrice, setCurrentPrice] = useState('');
  const [portfolioState, setPortfolioState] = useState({
    total_exposure: 0.3,
    average_correlation: 0.2,
    current_drawdown: 0.05,
    position_count: 3,
    largest_position_percent: 0.15,
    exchange_exposures: {
      binance: 0.2,
      hyperliquid: 0.1
    }
  });
  
  const { get, post } = useApi();
  const location = useLocation();
  
  useEffect(() => {
    // Auto-select first exchange and symbol if available
    if (exchanges.length > 0 && !selectedExchange) {
      setSelectedExchange(exchanges[0].id);
    }
    
    if (symbols.length > 0 && !selectedSymbol) {
      setSelectedSymbol(symbols[0].id);
    }
    
    // Check for setupId and recommendationId in URL query params
    const params = new URLSearchParams(location.search);
    const setupIdParam = params.get('setupId');
    const recommendationIdParam = params.get('recommendationId');
    const tabParam = params.get('tab');
    
    if (setupIdParam) {
      setSetupId(setupIdParam);
    }
    
    if (recommendationIdParam) {
      setRecommendationId(recommendationIdParam);
    }
    
    if (tabParam) {
      setTabValue(parseInt(tabParam, 10) || 0);
    }
  }, [exchanges, symbols, location.search]);
  
  const fetchRiskAssessment = async () => {
    if (!setupId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const params = { recommendation_id: recommendationId };
      const body = portfolioState;
      
      const response = await post(`/api/v1/assistant/risk-assessment/${setupId}`, body, { params });
      setRiskAssessment(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching risk assessment:', err);
      setError('Failed to load risk assessment. Please try again.');
      setLoading(false);
    }
  };
  
  const fetchChecklist = async () => {
    if (!setupId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const params = { recommendation_id: recommendationId };
      
      const response = await get(`/api/v1/assistant/checklist/${setupId}`, { params });
      setChecklist(response.data || []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching checklist:', err);
      setError('Failed to load trade checklist. Please try again.');
      setLoading(false);
    }
  };
  
  const fetchScenarios = async () => {
    if (!setupId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const params = { 
        recommendation_id: recommendationId,
        current_price: currentPrice || undefined
      };
      
      const response = await post(`/api/v1/assistant/scenarios/${setupId}`, {}, { params });
      setScenarios(response.data || {});
      setLoading(false);
    } catch (err) {
      console.error('Error fetching scenarios:', err);
      setError('Failed to load trade scenarios. Please try again.');
      setLoading(false);
    }
  };
  
  useEffect(() => {
    if (setupId) {
      if (tabValue === 0) {
        fetchRiskAssessment();
      } else if (tabValue === 1) {
        fetchChecklist();
      } else if (tabValue === 2) {
        fetchScenarios();
      }
    }
  }, [setupId, recommendationId, tabValue]);
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handlePortfolioStateChange = (field, value) => {
    setPortfolioState(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  const handleExchangeExposureChange = (exchange, value) => {
    setPortfolioState(prev => ({
      ...prev,
      exchange_exposures: {
        ...prev.exchange_exposures,
        [exchange]: value
      }
    }));
  };
  
  const handleChecklistItemToggle = (index) => {
    const newChecklist = [...checklist];
    newChecklist[index] = {
      ...newChecklist[index],
      auto_check: newChecklist[index].auto_check === null ? true : !newChecklist[index].auto_check
    };
    setChecklist(newChecklist);
  };
  
  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'very_low':
        return 'success';
      case 'low':
        return 'success';
      case 'moderate':
        return 'warning';
      case 'high':
        return 'error';
      case 'very_high':
        return 'error';
      default:
        return 'default';
    }
  };
  
  const getRiskLevelIcon = (riskLevel) => {
    switch (riskLevel) {
      case 'very_low':
      case 'low':
        return <CheckCircle />;
      case 'moderate':
        return <Info />;
      case 'high':
      case 'very_high':
        return <Warning />;
      default:
        return <Info />;
    }
  };
  
  const formatRiskLevel = (riskLevel) => {
    return riskLevel
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  const getChecklistCategoryIcon = (category) => {
    switch (category) {
      case 'setup_quality':
        return <Assessment />;
      case 'market_condition':
        return <BarChart />;
      case 'risk_management':
        return <Warning />;
      default:
        return <Info />;
    }
  };
  
  const getImportanceColor = (importance) => {
    switch (importance) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };
  
  const getScenarioIcon = (scenarioType) => {
    switch (scenarioType) {
      case 'best_case':
        return <ArrowUpward color="success" />;
      case 'worst_case':
        return <ArrowDownward color="error" />;
      default:
        return <Info />;
    }
  };
  
  const formatScenarioType = (scenarioType) => {
    return scenarioType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Trading Decision Support
      </Typography>
      <Typography variant="body2" color="textSecondary" paragraph>
        Get comprehensive decision support for your trading decisions, including risk assessment, trade validation, and scenario modeling.
      </Typography>
      
      {!setupId && (
        <Alert severity="info" sx={{ mb: 3 }}>
          To use the decision support tools, first select a trading setup from the Setup Detection tab or a recommendation from the Strategy Recommendations tab.
        </Alert>
      )}
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="Decision support tabs"
        >
          <Tab label="Risk Assessment" {...a11yProps(0)} />
          <Tab label="Trade Checklist" {...a11yProps(1)} />
          <Tab label="Scenario Modeling" {...a11yProps(2)} />
        </Tabs>
      </Box>
      
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Portfolio State
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  Adjust these values to reflect your current portfolio state for more accurate risk assessment.
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      label="Total Exposure"
                      type="number"
                      value={portfolioState.total_exposure}
                      onChange={(e) => handlePortfolioStateChange('total_exposure', parseFloat(e.target.value))}
                      fullWidth
                      margin="dense"
                      inputProps={{ step: 0.05, min: 0, max: 1 }}
                      helperText="Percentage of account in open positions (0-1)"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      label="Average Correlation"
                      type="number"
                      value={portfolioState.average_correlation}
                      onChange={(e) => handlePortfolioStateChange('average_correlation', parseFloat(e.target.value))}
                      fullWidth
                      margin="dense"
                      inputProps={{ step: 0.05, min: -1, max: 1 }}
                      helperText="Average correlation between positions (-1 to 1)"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      label="Current Drawdown"
                      type="number"
                      value={portfolioState.current_drawdown}
                      onChange={(e) => handlePortfolioStateChange('current_drawdown', parseFloat(e.target.value))}
                      fullWidth
                      margin="dense"
                      inputProps={{ step: 0.01, min: 0, max: 1 }}
                      helperText="Current drawdown from peak (0-1)"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      label="Position Count"
                      type="number"
                      value={portfolioState.position_count}
                      onChange={(e) => handlePortfolioStateChange('position_count', parseInt(e.target.value, 10))}
                      fullWidth
                      margin="dense"
                      inputProps={{ step: 1, min: 0 }}
                      helperText="Number of open positions"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      label="Largest Position %"
                      type="number"
                      value={portfolioState.largest_position_percent}
                      onChange={(e) => handlePortfolioStateChange('largest_position_percent', parseFloat(e.target.value))}
                      fullWidth
                      margin="dense"
                      inputProps={{ step: 0.05, min: 0, max: 1 }}
                      helperText="Size of largest position as % of account (0-1)"
                    />
                  </Grid>
                </Grid>
              </CardContent>
              <CardActions>
                <Button 
                  variant="contained" 
                  onClick={fetchRiskAssessment}
                  disabled={loading || !setupId}
                  fullWidth
                >
                  {loading ? <CircularProgress size={24} /> : 'Assess Risk'}
                </Button>
              </CardActions>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={8}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
            )}
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : !riskAssessment ? (
              <Alert severity="info">
                Click "Assess Risk" to generate a risk assessment for the selected setup.
              </Alert>
            ) : (
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h6">
                      Risk Assessment
                    </Typography>
                    <Chip 
                      icon={getRiskLevelIcon(riskAssessment.risk_level)} 
                      label={formatRiskLevel(riskAssessment.risk_level)} 
                      color={getRiskLevelColor(riskAssessment.risk_level)}
                    />
                  </Box>
                  
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" gutterBottom>
                      Risk Score: {riskAssessment.risk_score}/100
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={riskAssessment.risk_score} 
                      color={getRiskLevelColor(riskAssessment.risk_level)}
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        Risk Factors
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemText 
                            primary="Setup Quality" 
                            secondary={`${(riskAssessment.quality_factor * 100).toFixed(0)}%`} 
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Risk/Reward Ratio" 
                            secondary={riskAssessment.risk_reward_factor.toFixed(2)} 
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Position Sizing" 
                            secondary={riskAssessment.position_sizing} 
                          />
                        </ListItem>
                        {riskAssessment.market_regime && (
                          <ListItem>
                            <ListItemText 
                              primary="Market Regime" 
                              secondary={riskAssessment.market_regime} 
                            />
                          </ListItem>
                        )}
                        {riskAssessment.volatility_regime && (
                          <ListItem>
                            <ListItemText 
                              primary="Volatility Regime" 
                              secondary={riskAssessment.volatility_regime} 
                            />
                          </ListItem>
                        )}
                        {riskAssessment.liquidity_regime && (
                          <ListItem>
                            <ListItemText 
                              primary="Liquidity Regime" 
                              secondary={riskAssessment.liquidity_regime} 
                            />
                          </ListItem>
                        )}
                        <ListItem>
                          <ListItemText 
                            primary="Portfolio Adjustment" 
                            secondary={`${riskAssessment.portfolio_adjustment > 0 ? '+' : ''}${riskAssessment.portfolio_adjustment}`} 
                          />
                        </ListItem>
                      </List>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        Warnings
                      </Typography>
                      {riskAssessment.warnings.length === 0 ? (
                        <Alert severity="success" sx={{ mt: 1 }}>
                          No warnings detected for this trade.
                        </Alert>
                      ) : (
                        <List dense>
                          {riskAssessment.warnings.map((warning, index) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <Warning color="warning" />
                              </ListItemIcon>
                              <ListItemText primary={warning} />
                            </ListItem>
                          ))}
                        </List>
                      )}
                    </Grid>
                  </Grid>
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    onClick={() => setTabValue(1)}
                  >
                    View Trade Checklist
                  </Button>
                  <Button 
                    size="small" 
                    onClick={() => setTabValue(2)}
                  >
                    Model Scenarios
                  </Button>
                </CardActions>
              </Card>
            )}
          </Grid>
        </Grid>
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        )}
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        ) : checklist.length === 0 ? (
          <Alert severity="info">
            No checklist available. Please select a trading setup and generate a risk assessment first.
          </Alert>
        ) : (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Pre-Trade Checklist
            </Typography>
            <Typography variant="body2" color="textSecondary" paragraph>
              Use this checklist to validate your trade before execution. Check each item that you have confirmed.
            </Typography>
            
            <Grid container spacing={2}>
              {['setup_quality', 'market_condition', 'risk_management', 'entry_timing', 'exit_strategy', 'portfolio_context', 'psychological'].map((category) => {
                const categoryItems = checklist.filter(item => item.category === category);
                if (categoryItems.length === 0) return null;
                
                return (
                  <Grid item xs={12} key={category}>
                    <Accordion defaultExpanded>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ mr: 1 }}>
                            {getChecklistCategoryIcon(category)}
                          </Box>
                          <Typography variant="subtitle2">
                            {category.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                          </Typography>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List>
                          {categoryItems.map((item, index) => (
                            <ListItem 
                              key={index}
                              secondaryAction={
                                <Checkbox
                                  edge="end"
                                  checked={item.auto_check === true}
                                  onChange={() => handleChecklistItemToggle(checklist.indexOf(item))}
                                  icon={<CheckBoxOutlineBlank />}
                                  checkedIcon={<CheckBox />}
                                />
                              }
                            >
                              <ListItemText 
                                primary={
                                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <Typography variant="body2">
                                      {item.question}
                                    </Typography>
                                    <Chip 
                                      label={item.importance} 
                                      size="small" 
                                      color={getImportanceColor(item.importance)}
                                      sx={{ ml: 1 }}
                                    />
                                  </Box>
                                }
                                secondary={item.guidance}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                );
              })}
            </Grid>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
              <Button 
                variant="outlined" 
                onClick={() => setTabValue(0)}
              >
                Back to Risk Assessment
              </Button>
              
              <Button 
                variant="contained" 
                color="primary"
                disabled={checklist.some(item => item.importance === 'critical' && item.auto_check !== true)}
              >
                Proceed with Trade
              </Button>
            </Box>
          </Box>
        )}
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Scenario Parameters
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  Adjust these values to model different trade scenarios.
                </Typography>
                
                <TextField
                  label="Current Price"
                  type="number"
                  value={currentPrice}
                  onChange={(e) => setCurrentPrice(e.target.value)}
                  fullWidth
                  margin="normal"
                  helperText="Leave blank to use the latest market price"
                />
              </CardContent>
              <CardActions>
                <Button 
                  variant="contained" 
                  onClick={fetchScenarios}
                  disabled={loading || !setupId}
                  fullWidth
                >
                  {loading ? <CircularProgress size={24} /> : 'Model Scenarios'}
                </Button>
              </CardActions>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={8}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
            )}
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : Object.keys(scenarios).length === 0 ? (
              <Alert severity="info">
                Click "Model Scenarios" to generate trade scenarios for the selected setup.
              </Alert>
            ) : (
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Trade Scenarios
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  These scenarios model different possible outcomes for your trade.
                </Typography>
                
                <Grid container spacing={2}>
                  {Object.entries(scenarios).map(([type, scenario]) => (
                    <Grid item xs={12} sm={6} key={type}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <Box sx={{ mr: 1 }}>
                              {getScenarioIcon(type)}
                            </Box>
                            <Typography variant="subtitle2">
                              {formatScenarioType(type)}
                            </Typography>
                          </Box>
                          
                          <Typography variant="body2" paragraph>
                            {scenario.description}
                          </Typography>
                          
                          <Divider sx={{ my: 1 }} />
                          
                          <Stack spacing={1}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2">Entry Price:</Typography>
                              <Typography variant="body2">{scenario.entry_price}</Typography>
                            </Box>
                            
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2">Exit Price:</Typography>
                              <Typography variant="body2">{scenario.exit_price}</Typography>
                            </Box>
                            
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2">Stop Loss:</Typography>
                              <Typography variant="body2">{scenario.stop_loss}</Typography>
                            </Box>
                            
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2">P/L %:</Typography>
                              <Typography 
                                variant="body2" 
                                color={scenario.profit_loss_percent >= 0 ? 'success.main' : 'error.main'}
                              >
                                {scenario.profit_loss_percent >= 0 ? '+' : ''}{scenario.profit_loss_percent.toFixed(2)}%
                              </Typography>
                            </Box>
                            
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2">P/L (R):</Typography>
                              <Typography 
                                variant="body2" 
                                color={scenario.profit_loss_r >= 0 ? 'success.main' : 'error.main'}
                              >
                                {scenario.profit_loss_r >= 0 ? '+' : ''}{scenario.profit_loss_r.toFixed(2)}R
                              </Typography>
                            </Box>
                            
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2">Probability:</Typography>
                              <Typography variant="body2">{(scenario.normalized_probability * 100).toFixed(0)}%</Typography>
                            </Box>
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
                
                <Box sx={{ mt: 3 }}>
                  <Alert severity="info">
                    <Typography variant="body2">
                      <strong>Expected Value:</strong> {Object.values(scenarios)[0]?.expected_value.toFixed(2)}R
                    </Typography>
                  </Alert>
                </Box>
              </Box>
            )}
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
};

export default DecisionSupport; 