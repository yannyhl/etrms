import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Tabs,
  Tab,
  Chip,
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  ShowChart as ShowChartIcon,
  List as ListIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { api } from '../../services/api';
import { handleApiError } from '../../utils/errorHandler';
import { useAlert } from '../../hooks/useAlert';
import AlertMessage from '../AlertMessage';

/**
 * Component for displaying backtest results
 * 
 * @param {Object} props - Component props
 * @param {string} props.backtestId - ID of the backtest to display results for
 * @returns {React.ReactElement} The BacktestResults component
 */
const BacktestResults = ({ backtestId }) => {
  const [backtest, setBacktest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const { alert, showError, closeAlert } = useAlert();

  // Fetch backtest data when backtestId changes
  useEffect(() => {
    if (backtestId) {
      fetchBacktest();
    }
  }, [backtestId]);

  // Fetch backtest data from the API
  const fetchBacktest = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/backtest/${backtestId}`);
      setBacktest(response.data);
    } catch (error) {
      handleApiError(error, 'BacktestResults.fetchBacktest', showError);
    } finally {
      setLoading(false);
    }
  };

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Format date for display
  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy HH:mm:ss');
    } catch (err) {
      return dateString;
    }
  };

  // Format number as percentage
  const formatPercent = (value) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  // Format number as currency
  const formatCurrency = (value) => {
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // Get status chip for backtest status
  const getStatusChip = (status) => {
    switch (status) {
      case 'pending':
        return <Chip label="Pending" color="default" size="small" />;
      case 'running':
        return <Chip label="Running" color="primary" size="small" />;
      case 'completed':
        return <Chip label="Completed" color="success" size="small" />;
      case 'failed':
        return <Chip label="Failed" color="error" size="small" />;
      case 'cancelled':
        return <Chip label="Cancelled" color="warning" size="small" />;
      default:
        return <Chip label={status} color="default" size="small" />;
    }
  };

  if (!backtestId) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body1" color="textSecondary" align="center">
            No backtest selected. Please select a backtest from the history tab.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (loading && !backtest) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!backtest) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body1" color="textSecondary" align="center">
            Failed to load backtest results. Please try again.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" component="h2">
            {backtest.name} Results
          </Typography>
          {getStatusChip(backtest.status)}
        </Box>

        <AlertMessage
          open={alert.open}
          type={alert.type}
          message={alert.message}
          onClose={closeAlert}
        />

        {/* Backtest Summary */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Type
              </Typography>
              <Typography variant="body1">
                {backtest.type.charAt(0).toUpperCase() + backtest.type.slice(1).replace('_', ' ')}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Date Range
              </Typography>
              <Typography variant="body1">
                {formatDate(backtest.start_date)} - {formatDate(backtest.end_date)}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Exchanges
              </Typography>
              <Typography variant="body1">
                {backtest.exchanges.join(', ')}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Symbols
              </Typography>
              <Typography variant="body1">
                {backtest.symbols.join(', ')}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Timeframe
              </Typography>
              <Typography variant="body1">
                {backtest.timeframe}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Initial Capital
              </Typography>
              <Typography variant="body1">
                {formatCurrency(backtest.initial_capital)}
              </Typography>
            </Grid>
          </Grid>
        </Paper>

        {/* Results Tabs */}
        {backtest.status === 'completed' && backtest.result && (
          <>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              variant="fullWidth"
              indicatorColor="primary"
              textColor="primary"
              aria-label="Backtest results tabs"
              sx={{ mb: 2 }}
            >
              <Tab icon={<ShowChartIcon />} label="Metrics" />
              <Tab icon={<ListIcon />} label="Trades" />
              <Tab icon={<WarningIcon />} label="Circuit Breakers" />
            </Tabs>

            <TabPanel value={tabValue} index={0}>
              <MetricsPanel metrics={backtest.result.metrics} />
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <TradesPanel trades={backtest.result.trades} />
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <CircuitBreakersPanel events={backtest.result.circuit_breaker_events} />
            </TabPanel>
          </>
        )}

        {/* Status Messages */}
        {backtest.status === 'pending' && (
          <Typography variant="body1" color="textSecondary" align="center">
            Backtest is pending execution. Results will be available once the backtest is complete.
          </Typography>
        )}

        {backtest.status === 'running' && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 3 }}>
            <CircularProgress sx={{ mb: 2 }} />
            <Typography variant="body1" color="textSecondary" align="center">
              Backtest is running. Results will be available once the backtest is complete.
            </Typography>
          </Box>
        )}

        {backtest.status === 'failed' && (
          <Paper sx={{ p: 2, bgcolor: 'error.dark' }}>
            <Typography variant="subtitle1" color="error.contrastText">
              Backtest Failed
            </Typography>
            <Typography variant="body1" color="error.contrastText">
              {backtest.result?.error || 'An unknown error occurred during the backtest.'}
            </Typography>
          </Paper>
        )}

        {backtest.status === 'cancelled' && (
          <Typography variant="body1" color="textSecondary" align="center">
            Backtest was cancelled. No results are available.
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

// TabPanel component for tab content
const TabPanel = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`backtest-results-tabpanel-${index}`}
      aria-labelledby={`backtest-results-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
};

// Metrics Panel component
const MetricsPanel = ({ metrics }) => {
  if (!metrics) {
    return (
      <Typography variant="body1" color="textSecondary" align="center">
        No metrics available.
      </Typography>
    );
  }

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6} lg={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            Total Return
          </Typography>
          <Typography variant="h5" color={metrics.total_return >= 0 ? 'success.main' : 'error.main'}>
            {(metrics.total_return * 100).toFixed(2)}%
          </Typography>
        </Paper>
      </Grid>
      <Grid item xs={12} md={6} lg={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            Win Rate
          </Typography>
          <Typography variant="h5">
            {(metrics.win_rate * 100).toFixed(2)}%
          </Typography>
        </Paper>
      </Grid>
      <Grid item xs={12} md={6} lg={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            Profit Factor
          </Typography>
          <Typography variant="h5">
            {metrics.profit_factor.toFixed(2)}
          </Typography>
        </Paper>
      </Grid>
      <Grid item xs={12} md={6} lg={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            Max Drawdown
          </Typography>
          <Typography variant="h5" color="error.main">
            {(metrics.max_drawdown * 100).toFixed(2)}%
          </Typography>
        </Paper>
      </Grid>
      <Grid item xs={12} md={6} lg={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            Sharpe Ratio
          </Typography>
          <Typography variant="h5">
            {metrics.sharpe_ratio.toFixed(2)}
          </Typography>
        </Paper>
      </Grid>
      <Grid item xs={12} md={6} lg={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            Total Trades
          </Typography>
          <Typography variant="h5">
            {metrics.total_trades}
          </Typography>
        </Paper>
      </Grid>
    </Grid>
  );
};

// Trades Panel component
const TradesPanel = ({ trades }) => {
  if (!trades || trades.length === 0) {
    return (
      <Typography variant="body1" color="textSecondary" align="center">
        No trades available.
      </Typography>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Exchange</TableCell>
            <TableCell>Side</TableCell>
            <TableCell>Entry Price</TableCell>
            <TableCell>Exit Price</TableCell>
            <TableCell>Quantity</TableCell>
            <TableCell>PnL</TableCell>
            <TableCell>PnL %</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {trades.map((trade) => (
            <TableRow key={trade.id}>
              <TableCell>{trade.symbol}</TableCell>
              <TableCell>{trade.exchange}</TableCell>
              <TableCell>{trade.side}</TableCell>
              <TableCell>${trade.entry_price.toLocaleString()}</TableCell>
              <TableCell>${trade.exit_price.toLocaleString()}</TableCell>
              <TableCell>{trade.quantity}</TableCell>
              <TableCell
                sx={{
                  color: trade.pnl >= 0 ? 'success.main' : 'error.main',
                }}
              >
                ${trade.pnl.toLocaleString()}
              </TableCell>
              <TableCell
                sx={{
                  color: trade.pnl_percent >= 0 ? 'success.main' : 'error.main',
                }}
              >
                {(trade.pnl_percent * 100).toFixed(2)}%
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

// Circuit Breakers Panel component
const CircuitBreakersPanel = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <Typography variant="body1" color="textSecondary" align="center">
        No circuit breaker events occurred during the backtest.
      </Typography>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Time</TableCell>
            <TableCell>Circuit Breaker</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Condition</TableCell>
            <TableCell>Threshold</TableCell>
            <TableCell>Value</TableCell>
            <TableCell>Action</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {events.map((event) => (
            <TableRow key={event.id}>
              <TableCell>{format(new Date(event.timestamp), 'MMM d, yyyy HH:mm:ss')}</TableCell>
              <TableCell>{event.circuit_breaker_name}</TableCell>
              <TableCell>{event.type}</TableCell>
              <TableCell>{event.condition}</TableCell>
              <TableCell>{event.threshold}</TableCell>
              <TableCell>{event.value}</TableCell>
              <TableCell>{event.action}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

BacktestResults.propTypes = {
  backtestId: PropTypes.string,
};

TabPanel.propTypes = {
  children: PropTypes.node,
  value: PropTypes.number.isRequired,
  index: PropTypes.number.isRequired,
};

MetricsPanel.propTypes = {
  metrics: PropTypes.object,
};

TradesPanel.propTypes = {
  trades: PropTypes.array,
};

CircuitBreakersPanel.propTypes = {
  events: PropTypes.array,
};

export default BacktestResults; 