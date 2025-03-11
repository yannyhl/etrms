import React, { useState } from 'react';
import {
  Box,
  Container,
  Tab,
  Tabs,
  Paper,
} from '@mui/material';
import {
  History as HistoryIcon,
  Add as AddIcon,
  Timeline as TimelineIcon,
  Tune as TuneIcon,
} from '@mui/icons-material';
import PageHeader from '../components/PageHeader';
import BacktestList from '../components/backtesting/BacktestList';
import BacktestForm from '../components/backtesting/BacktestForm';
import BacktestResults from '../components/backtesting/BacktestResults';
import BacktestOptimization from '../components/backtesting/BacktestOptimization';

/**
 * Backtesting page with tabs for different backtesting features
 */
const Backtesting = () => {
  const [tabValue, setTabValue] = useState(0);
  const [selectedBacktestId, setSelectedBacktestId] = useState(null);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleBacktestSelect = (backtestId) => {
    setSelectedBacktestId(backtestId);
    setTabValue(2); // Switch to Results tab
  };

  const handleBacktestCreated = (backtestId) => {
    setSelectedBacktestId(backtestId);
    setTabValue(0); // Switch to History tab
  };

  return (
    <Container maxWidth="lg">
      <PageHeader
        title="Backtesting"
        description="Test your risk management strategies against historical data"
      />
      
      <Paper sx={{ mb: 4 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="fullWidth"
          indicatorColor="primary"
          textColor="primary"
          aria-label="Backtesting tabs"
        >
          <Tab icon={<HistoryIcon />} label="History" />
          <Tab icon={<AddIcon />} label="New Backtest" />
          <Tab 
            icon={<TimelineIcon />} 
            label="Results" 
            disabled={!selectedBacktestId}
          />
          <Tab icon={<TuneIcon />} label="Optimization" />
        </Tabs>
      </Paper>
      
      <TabPanel value={tabValue} index={0}>
        <BacktestList onBacktestSelect={handleBacktestSelect} />
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        <BacktestForm onBacktestCreated={handleBacktestCreated} />
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        <BacktestResults backtestId={selectedBacktestId} />
      </TabPanel>
      
      <TabPanel value={tabValue} index={3}>
        <BacktestOptimization />
      </TabPanel>
    </Container>
  );
};

// TabPanel component for tab content
const TabPanel = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`backtesting-tabpanel-${index}`}
      aria-labelledby={`backtesting-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

export default Backtesting; 