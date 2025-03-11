import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Grid,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  ArrowUpward,
  ArrowDownward,
  Warning,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useWebSocket } from '../hooks/useWebSocket';
import { Channels } from '../utils/constants';
import { formatCurrency, formatPercentage } from '../utils/formatters';

const RiskIndicator = ({ value, thresholds, reverseColor = false }) => {
  let color = 'success';
  
  if (reverseColor) {
    if (value > thresholds.critical) color = 'error';
    else if (value > thresholds.warning) color = 'warning';
  } else {
    if (value < thresholds.critical) color = 'error';
    else if (value < thresholds.warning) color = 'warning';
  }
  
  return (
    <Chip 
      color={color} 
      size="small" 
      label={formatPercentage(value)}
      icon={color === 'error' ? <Warning /> : color === 'warning' ? <Warning /> : <CheckCircle />} 
    />
  );
};

const MetricCard = ({ title, value, formatter, change, thresholds, reverseColor = false }) => {
  const formattedValue = formatter ? formatter(value) : value;
  const changeIcon = change > 0 ? <ArrowUpward fontSize="small" color="success" /> : <ArrowDownward fontSize="small" color="error" />;
  const changeColor = change > 0 ? 'success.main' : 'error.main';
  
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardHeader
        title={title}
        titleTypographyProps={{ variant: 'subtitle1' }}
        action={thresholds && <RiskIndicator value={value} thresholds={thresholds} reverseColor={reverseColor} />}
      />
      <CardContent>
        <Typography variant="h5" component="div" gutterBottom>
          {formattedValue}
        </Typography>
        {change !== undefined && (
          <Box display="flex" alignItems="center">
            {changeIcon}
            <Typography variant="body2" color={changeColor} sx={{ ml: 0.5 }}>
              {Math.abs(change).toFixed(2)}%
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

const RiskExposureBar = ({ exposure }) => {
  let color = 'success.main';
  if (exposure > 150) color = 'error.main';
  else if (exposure > 100) color = 'warning.main';
  
  return (
    <Box sx={{ width: '100%', mb: 2 }}>
      <Box display="flex" justifyContent="space-between" mb={1}>
        <Typography variant="body2">Exposure</Typography>
        <Typography variant="body2" color={color}>
          {formatPercentage(exposure)}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.min(exposure, 200)}
        color={exposure > 150 ? "error" : exposure > 100 ? "warning" : "success"}
        sx={{ height: 10, borderRadius: 5 }}
      />
      <Box display="flex" justifyContent="space-between" mt={0.5}>
        <Typography variant="caption">0%</Typography>
        <Typography variant="caption">50%</Typography>
        <Typography variant="caption">100%</Typography>
        <Typography variant="caption">150%</Typography>
        <Typography variant="caption">200%+</Typography>
      </Box>
    </Box>
  );
};

const PositionsTable = ({ positions }) => {
  if (!positions || positions.length === 0) {
    return (
      <Box textAlign="center" py={3}>
        <Typography variant="body1" color="textSecondary">
          No open positions
        </Typography>
      </Box>
    );
  }
  
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Exchange</TableCell>
            <TableCell align="right">Size</TableCell>
            <TableCell align="right">Value</TableCell>
            <TableCell align="right">PnL</TableCell>
            <TableCell align="right">Risk %</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {positions.map((position) => (
            <TableRow key={`${position.exchange}-${position.symbol}`}>
              <TableCell component="th" scope="row">
                {position.symbol}
              </TableCell>
              <TableCell>{position.exchange}</TableCell>
              <TableCell align="right">
                {position.quantity > 0 ? '+' : ''}{position.quantity}
              </TableCell>
              <TableCell align="right">{formatCurrency(position.notional_value)}</TableCell>
              <TableCell 
                align="right" 
                sx={{ 
                  color: position.unrealized_pnl > 0 ? 'success.main' : 'error.main'
                }}
              >
                {formatCurrency(position.unrealized_pnl)}
              </TableCell>
              <TableCell align="right">
                <Chip 
                  label={formatPercentage(position.risk_percentage || 0)} 
                  size="small"
                  color={
                    (position.risk_percentage || 0) > 5 ? 'error' : 
                    (position.risk_percentage || 0) > 2 ? 'warning' : 'success'
                  }
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

const ConnectionStatus = ({ connected, lastUpdated }) => {
  return (
    <Box display="flex" alignItems="center" mb={2}>
      <Chip 
        color={connected ? "success" : "error"}
        size="small"
        label={connected ? "Connected" : "Disconnected"}
        sx={{ mr: 2 }}
      />
      {lastUpdated && (
        <Typography variant="caption" color="textSecondary">
          Last updated: {format(new Date(lastUpdated), 'MMM d, yyyy HH:mm:ss')}
        </Typography>
      )}
    </Box>
  );
};

export const RiskDashboard = () => {
  const [riskMetrics, setRiskMetrics] = useState({
    total_equity: 0,
    total_margin_balance: 0,
    total_unrealized_pnl: 0,
    total_position_value: 0,
    current_drawdown: 0,
    max_drawdown: 0,
    exposure_percentage: 0,
    leverage: 0,
    risk_percentage: 0,
    position_count: 0,
    positions: [],
    largest_position: null,
    daily_pnl: 0,
    daily_pnl_percentage: 0,
    weekly_pnl: 0,
    weekly_pnl_percentage: 0,
    monthly_pnl: 0,
    monthly_pnl_percentage: 0,
  });
  
  const [lastUpdated, setLastUpdated] = useState(null);
  
  const { 
    data: riskData, 
    isConnected: riskConnected 
  } = useWebSocket(Channels.RISK_METRICS);
  
  // Process WebSocket data when received
  useEffect(() => {
    if (riskData) {
      setLastUpdated(new Date());
      
      // Extract risk metrics from WebSocket data
      let metricsData;
      if (riskData.risk_metrics) {
        metricsData = riskData.risk_metrics;
      } else if (riskData.data && riskData.data.risk_metrics) {
        metricsData = riskData.data.risk_metrics;
      } else if (riskData.data) {
        metricsData = riskData.data;
      } else {
        metricsData = riskData;
      }
      
      setRiskMetrics(prevMetrics => ({
        ...prevMetrics,
        ...metricsData
      }));
    }
  }, [riskData]);
  
  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h5" gutterBottom>
          Risk Dashboard
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          Real-time risk monitoring across all connected exchanges.
        </Typography>
        <ConnectionStatus connected={riskConnected} lastUpdated={lastUpdated} />
      </Box>
      
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={3}>
          <MetricCard 
            title="Total Equity" 
            value={riskMetrics.total_equity} 
            formatter={formatCurrency} 
            change={riskMetrics.daily_pnl_percentage}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard 
            title="Position Value" 
            value={riskMetrics.total_position_value} 
            formatter={formatCurrency} 
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard 
            title="Unrealized P&L" 
            value={riskMetrics.total_unrealized_pnl} 
            formatter={formatCurrency} 
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard 
            title="Active Positions" 
            value={riskMetrics.position_count} 
          />
        </Grid>
      </Grid>
      
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={4}>
          <Card variant="outlined">
            <CardHeader title="Exposure" titleTypographyProps={{ variant: 'subtitle1' }} />
            <CardContent>
              <RiskExposureBar exposure={riskMetrics.exposure_percentage || 0} />
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Leverage</Typography>
                  <Typography variant="h6">{riskMetrics.leverage?.toFixed(2)}x</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Risk %</Typography>
                  <Typography variant="h6">{formatPercentage(riskMetrics.risk_percentage || 0)}</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card variant="outlined">
            <CardHeader title="Drawdown" titleTypographyProps={{ variant: 'subtitle1' }} />
            <CardContent>
              <Box mb={2}>
                <Typography variant="body2" color="textSecondary" gutterBottom>Current Drawdown</Typography>
                <Typography variant="h6" color={
                  riskMetrics.current_drawdown > 15 ? 'error.main' : 
                  riskMetrics.current_drawdown > 10 ? 'warning.main' : 'text.primary'
                }>
                  {formatPercentage(riskMetrics.current_drawdown || 0)}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(riskMetrics.current_drawdown || 0, 25)}
                  color={
                    riskMetrics.current_drawdown > 15 ? "error" : 
                    riskMetrics.current_drawdown > 10 ? "warning" : "success"
                  }
                  sx={{ height: 6, borderRadius: 5, mt: 1 }}
                />
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Daily P&L</Typography>
                  <Typography variant="h6" color={
                    riskMetrics.daily_pnl >= 0 ? 'success.main' : 'error.main'
                  }>
                    {formatPercentage(riskMetrics.daily_pnl_percentage || 0)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Weekly P&L</Typography>
                  <Typography variant="h6" color={
                    riskMetrics.weekly_pnl >= 0 ? 'success.main' : 'error.main'
                  }>
                    {formatPercentage(riskMetrics.weekly_pnl_percentage || 0)}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card variant="outlined">
            <CardHeader title="Largest Position" titleTypographyProps={{ variant: 'subtitle1' }} />
            <CardContent>
              {riskMetrics.largest_position ? (
                <>
                  <Box mb={2}>
                    <Typography variant="h6">
                      {riskMetrics.largest_position.symbol}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {riskMetrics.largest_position.exchange}
                    </Typography>
                  </Box>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">Position Value</Typography>
                      <Typography variant="h6">
                        {formatCurrency(riskMetrics.largest_position.value || 0)}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">% of Equity</Typography>
                      <Typography variant="h6" color={
                        (riskMetrics.largest_position.percentage_of_equity || 0) > 20 ? 'error.main' : 
                        (riskMetrics.largest_position.percentage_of_equity || 0) > 10 ? 'warning.main' : 'text.primary'
                      }>
                        {formatPercentage(riskMetrics.largest_position.percentage_of_equity || 0)}
                      </Typography>
                    </Grid>
                  </Grid>
                </>
              ) : (
                <Box display="flex" justifyContent="center" alignItems="center" height={120}>
                  <Typography variant="body1" color="textSecondary">
                    No open positions
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Box mb={4}>
        <Typography variant="h6" gutterBottom>
          Open Positions
        </Typography>
        <PositionsTable positions={riskMetrics.positions || []} />
      </Box>
      
      <Box mb={4}>
        <Typography variant="h6" gutterBottom>
          Exchange Risk Summary
        </Typography>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Exchange</TableCell>
                <TableCell align="right">Equity</TableCell>
                <TableCell align="right">Available</TableCell>
                <TableCell align="right">Positions</TableCell>
                <TableCell align="right">Exposure</TableCell>
                <TableCell align="right">Unrealized P&L</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(riskMetrics.exchanges || {}).map(([exchange, data]) => (
                <TableRow key={exchange}>
                  <TableCell component="th" scope="row">
                    {exchange}
                  </TableCell>
                  <TableCell align="right">
                    {formatCurrency(data.equity || 0)}
                  </TableCell>
                  <TableCell align="right">
                    {formatCurrency(data.available_balance || 0)}
                  </TableCell>
                  <TableCell align="right">
                    {data.position_count || 0}
                  </TableCell>
                  <TableCell align="right">
                    <Chip 
                      label={formatPercentage(data.exposure_percentage || 0)} 
                      size="small"
                      color={
                        (data.exposure_percentage || 0) > 150 ? 'error' : 
                        (data.exposure_percentage || 0) > 100 ? 'warning' : 'success'
                      }
                    />
                  </TableCell>
                  <TableCell 
                    align="right" 
                    sx={{ 
                      color: (data.unrealized_pnl || 0) >= 0 ? 'success.main' : 'error.main'
                    }}
                  >
                    {formatCurrency(data.unrealized_pnl || 0)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
}; 