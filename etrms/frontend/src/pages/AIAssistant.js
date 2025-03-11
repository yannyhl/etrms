import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Tabs, 
  Tab, 
  CircularProgress, 
  Alert 
} from '@mui/material';
import { 
  Psychology, 
  TrendingUp, 
  BarChart, 
  SupportAgent 
} from '@mui/icons-material';
import { useApi } from '../hooks/useApi';
import SetupDetection from '../components/ai/SetupDetection';
import StrategyRecommendations from '../components/ai/StrategyRecommendations';
import DecisionSupport from '../components/ai/DecisionSupport';
import PerformanceAnalysis from '../components/ai/PerformanceAnalysis';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ai-assistant-tabpanel-${index}`}
      aria-labelledby={`ai-assistant-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index) {
  return {
    id: `ai-assistant-tab-${index}`,
    'aria-controls': `ai-assistant-tabpanel-${index}`,
  };
}

const AIAssistant = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exchanges, setExchanges] = useState([]);
  const [symbols, setSymbols] = useState({});
  
  const { get } = useApi();
  
  useEffect(() => {
    const fetchExchangesAndSymbols = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch available exchanges
        const exchangesResponse = await get('/api/v1/exchanges');
        if (exchangesResponse.status === 'success') {
          setExchanges(exchangesResponse.data);
          
          // Fetch symbols for each exchange
          const symbolsData = {};
          for (const exchange of exchangesResponse.data) {
            const symbolsResponse = await get(`/api/v1/exchanges/${exchange}/symbols`);
            if (symbolsResponse.status === 'success') {
              symbolsData[exchange] = symbolsResponse.data;
            }
          }
          setSymbols(symbolsData);
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching exchanges and symbols:', err);
        setError('Failed to load exchanges and symbols. Please try again later.');
        setLoading(false);
      }
    };
    
    fetchExchangesAndSymbols();
  }, [get]);
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        AI Trading Assistant
      </Typography>
      
      <Typography variant="body1" paragraph>
        The AI Trading Assistant helps you identify trading opportunities, develop strategies, 
        validate trading decisions, and analyze your performance.
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
      )}
      
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
          aria-label="AI Assistant tabs"
        >
          <Tab icon={<Psychology />} label="Setup Detection" {...a11yProps(0)} />
          <Tab icon={<TrendingUp />} label="Strategy Recommendations" {...a11yProps(1)} />
          <Tab icon={<SupportAgent />} label="Decision Support" {...a11yProps(2)} />
          <Tab icon={<BarChart />} label="Performance Analysis" {...a11yProps(3)} />
        </Tabs>
      </Paper>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TabPanel value={tabValue} index={0}>
            <SetupDetection exchanges={exchanges} symbols={symbols} />
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <StrategyRecommendations exchanges={exchanges} symbols={symbols} />
          </TabPanel>
          
          <TabPanel value={tabValue} index={2}>
            <DecisionSupport exchanges={exchanges} symbols={symbols} />
          </TabPanel>
          
          <TabPanel value={tabValue} index={3}>
            <PerformanceAnalysis />
          </TabPanel>
        </>
      )}
    </Box>
  );
};

export default AIAssistant; 