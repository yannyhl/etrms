import React, { useState, useEffect } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  CardHeader,
  Container,
  Divider,
  Grid,
  Paper,
  Typography,
  CircularProgress,
} from '@mui/material';
import {
  AccountBalance as AccountBalanceIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { api } from '../services/api';
import PageHeader from '../components/PageHeader';

// Metric card component for displaying key metrics
const MetricCard = ({ title, value, icon, color }) => {
  const IconComponent = icon;
  
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '50%',
              width: 40,
              height: 40,
              backgroundColor: `${color}.light`,
              color: `${color}.main`,
              mr: 2,
            }}
          >
            <IconComponent />
          </Box>
          <Typography variant="h6" color="textSecondary">
            {title}
          </Typography>
        </Box>
        <Typography variant="h4">{value}</Typography>
      </CardContent>
    </Card>
  );
};

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accountInfo, setAccountInfo] = useState(null);
  const [riskMetrics, setRiskMetrics] = useState(null);
  const [activeCircuitBreakers, setActiveCircuitBreakers] = useState([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Fetch account information
        const accountResponse = await api.get('/accounts/summary');
        setAccountInfo(accountResponse.data);
        
        // Fetch risk metrics
        const riskResponse = await api.getRiskMetrics();
        setRiskMetrics(riskResponse);
        
        // Fetch active circuit breakers
        const breakersResponse = await api.getCircuitBreakers({ enabled: true });
        setActiveCircuitBreakers(breakersResponse);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
    
    // Set up polling for real-time updates (every 30 seconds)
    const intervalId = setInterval(fetchDashboardData, 30000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  if (loading && !accountInfo) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <PageHeader
        title="Dashboard"
        description="Overview of your trading activity and risk metrics"
      />
      
      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}
      
      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Balance"
            value={accountInfo ? `$${accountInfo.totalBalance.toLocaleString()}` : '-'}
            icon={AccountBalanceIcon}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="PnL (24h)"
            value={accountInfo ? `$${accountInfo.dailyPnl.toLocaleString()}` : '-'}
            icon={TrendingUpIcon}
            color={accountInfo && accountInfo.dailyPnl >= 0 ? 'success' : 'error'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Risk Score"
            value={riskMetrics ? riskMetrics.riskScore.toFixed(2) : '-'}
            icon={WarningIcon}
            color={riskMetrics && riskMetrics.riskScore < 50 ? 'success' : 
                  riskMetrics && riskMetrics.riskScore < 75 ? 'warning' : 'error'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Breakers"
            value={activeCircuitBreakers ? activeCircuitBreakers.length : '-'}
            icon={SecurityIcon}
            color="info"
          />
        </Grid>
      </Grid>
      
      {/* Position Summary */}
      <Card sx={{ mb: 4 }}>
        <CardHeader title="Active Positions" />
        <Divider />
        <CardContent>
          {accountInfo && accountInfo.positions && accountInfo.positions.length > 0 ? (
            <Grid container spacing={2}>
              {accountInfo.positions.map((position) => (
                <Grid item xs={12} sm={6} md={4} key={position.symbol}>
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      borderLeft: 6,
                      borderColor: position.unrealizedPnl >= 0 ? 'success.main' : 'error.main',
                    }}
                  >
                    <Typography variant="h6">{position.symbol}</Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                      <Typography variant="body2" color="textSecondary">
                        Size:
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {position.size} {position.side}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="textSecondary">
                        Entry:
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        ${position.entryPrice.toLocaleString()}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="textSecondary">
                        Mark:
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        ${position.markPrice.toLocaleString()}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="textSecondary">
                        PnL:
                      </Typography>
                      <Typography
                        variant="body1"
                        fontWeight="bold"
                        color={position.unrealizedPnl >= 0 ? 'success.main' : 'error.main'}
                      >
                        ${position.unrealizedPnl.toLocaleString()}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Typography variant="body1" color="textSecondary" align="center">
              No active positions
            </Typography>
          )}
        </CardContent>
      </Card>
      
      {/* Active Circuit Breakers */}
      <Card>
        <CardHeader title="Active Circuit Breakers" />
        <Divider />
        <CardContent>
          {activeCircuitBreakers && activeCircuitBreakers.length > 0 ? (
            <Grid container spacing={2}>
              {activeCircuitBreakers.map((breaker) => (
                <Grid item xs={12} sm={6} md={4} key={breaker.id}>
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      borderLeft: 6,
                      borderColor: 'warning.main',
                    }}
                  >
                    <Typography variant="h6">{breaker.name}</Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                      <Typography variant="body2" color="textSecondary">
                        Type:
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {breaker.type}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="textSecondary">
                        Threshold:
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {breaker.threshold}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="textSecondary">
                        Action:
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {breaker.action}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Typography variant="body1" color="textSecondary" align="center">
              No active circuit breakers
            </Typography>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

export default Dashboard; 