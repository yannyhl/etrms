import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Grid,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  BarChart as BarChartIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  PieChart as PieChartIcon,
  Science as ScienceIcon
} from '@mui/icons-material';
import { useApi } from '../hooks/useApi';
import { API_BASE_URL } from '../config';

// Import custom components
import BasicBacktestForm from '../components/backtesting/BasicBacktestForm';
import BacktestResults from '../components/backtesting/BacktestResults';
import ParameterOptimizationForm from '../components/backtesting/ParameterOptimizationForm';
import OptimizationResults from '../components/backtesting/OptimizationResults';
import WalkForwardForm from '../components/backtesting/WalkForwardForm';
import WalkForwardResults from '../components/backtesting/WalkForwardResults';
import MonteCarloForm from '../components/backtesting/MonteCarloForm';
import MonteCarloResults from '../components/backtesting/MonteCarloResults';
import TasksList from '../components/backtesting/TasksList';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`backtesting-tabpanel-${index}`}
      aria-labelledby={`backtesting-tab-${index}`}
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
    id: `backtesting-tab-${index}`,
    'aria-controls': `backtesting-tabpanel-${index}`,
  };
}

function Backtesting() {
  const [selectedTabIndex, setSelectedTabIndex] = useState(0);
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [activeMonteCarloTask, setActiveMonteCarloTask] = useState(null);
  const [monteCarloSimulationId, setMonteCarloSimulationId] = useState(null);
  
  const { get } = useApi();

  useEffect(() => {
    fetchTasks();
    fetchStrategies();
  }, []);

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      const response = await get(`${API_BASE_URL}/backtest/tasks`);
      if (response.status === 'success') {
        setTasks(response.data || []);
      } else {
        setError('Failed to fetch tasks');
      }
    } catch (err) {
      setError('Error fetching tasks: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStrategies = async () => {
    try {
      const response = await get(`${API_BASE_URL}/strategies`);
      if (response.status === 'success') {
        setAvailableStrategies(response.data || []);
      }
    } catch (err) {
      console.error('Error fetching strategies:', err);
    }
  };

  const handleTaskSelect = (task) => {
    setSelectedTask(task);
  };

  const handleTaskCreated = () => {
    fetchTasks();
  };

  const handleMonteCarloComplete = (simulationData) => {
    setMonteCarloSimulationId(simulationData.monte_carlo_id);
  };

  const handleTabChange = (event, newValue) => {
    setSelectedTabIndex(newValue);
  };

  return (
    <Box sx={{ py: 4, px: 2 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Backtesting
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Test and optimize your trading strategies with historical data
        </Typography>
      </Box>

      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={selectedTabIndex}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
          aria-label="Backtesting tabs"
        >
          <Tab icon={<BarChartIcon />} label="Backtests" {...a11yProps(0)} />
          <Tab icon={<SettingsIcon />} label="Parameter Optimization" {...a11yProps(1)} />
          <Tab icon={<RefreshIcon />} label="Walk-Forward Analysis" {...a11yProps(2)} />
          <Tab icon={<PieChartIcon />} label="Monte Carlo" {...a11yProps(3)} />
          <Tab icon={<ScienceIcon />} label="Tasks" {...a11yProps(4)} />
        </Tabs>

        {/* Backtest Tab */}
        <TabPanel value={selectedTabIndex} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Configure Backtest
                </Typography>
                <BasicBacktestForm 
                  strategies={availableStrategies} 
                  onSubmit={handleTaskCreated}
                  loading={isLoading}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Backtest Results
                </Typography>
                <BacktestResults selectedTask={selectedTask} />
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Parameter Optimization Tab */}
        <TabPanel value={selectedTabIndex} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Configure Optimization
                </Typography>
                <ParameterOptimizationForm 
                  strategies={availableStrategies} 
                  onSubmit={handleTaskCreated}
                  loading={isLoading}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Optimization Results
                </Typography>
                <OptimizationResults selectedTask={selectedTask} />
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Walk-Forward Analysis Tab */}
        <TabPanel value={selectedTabIndex} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Configure Walk-Forward Analysis
                </Typography>
                <WalkForwardForm 
                  strategies={availableStrategies} 
                  onSubmit={handleTaskCreated}
                  loading={isLoading}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Walk-Forward Results
                </Typography>
                <WalkForwardResults selectedTask={selectedTask} />
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Monte Carlo Tab */}
        <TabPanel value={selectedTabIndex} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Configure Monte Carlo Simulation
                </Typography>
                <MonteCarloForm 
                  tasks={tasks} 
                  onSubmit={handleTaskCreated}
                  onComplete={handleMonteCarloComplete}
                  loading={isLoading}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Monte Carlo Results
                </Typography>
                <MonteCarloResults 
                  selectedTask={selectedTask}
                  simulationId={monteCarloSimulationId}
                />
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tasks Tab */}
        <TabPanel value={selectedTabIndex} index={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Backtesting Tasks
            </Typography>
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : error ? (
              <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
            ) : (
              <TasksList 
                tasks={tasks} 
                onTaskSelect={handleTaskSelect} 
                onTasksRefresh={fetchTasks} 
              />
            )}
          </Paper>
        </TabPanel>
      </Paper>
    </Box>
  );
}

export default Backtesting; 