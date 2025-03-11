import React, { useState, useEffect, useRef } from 'react';
import { 
  Card, CardHeader, CardContent, 
  Grid, Typography, Alert, CircularProgress, 
  Box, Divider, Paper, 
  Table, TableBody, TableCell, TableContainer, TableRow,
  Tooltip, LinearProgress
} from '@mui/material';
import axios from 'axios';
import { API_BASE_URL } from '../../config';
import Chart from 'react-apexcharts';

/**
 * MonteCarloResults component for displaying the results of a Monte Carlo simulation.
 * 
 * @param {Object} props - Component props
 * @param {string} props.simulationId - The ID of the Monte Carlo simulation to display
 */
function MonteCarloResults({ simulationId }) {
  // State for simulation results
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Charts references
  const equityCurvesChartRef = useRef(null);
  const balanceDistributionChartRef = useRef(null);
  const drawdownDistributionChartRef = useRef(null);

  // Fetch simulation results
  useEffect(() => {
    const fetchResults = async () => {
      if (!simulationId) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await axios.get(
          `${API_BASE_URL}/backtest/monte-carlo/results/${simulationId}`
        );
        setResults(response.data);
        setIsLoading(false);
      } catch (err) {
        setIsLoading(false);
        if (err.response && err.response.data) {
          setError(err.response.data.message || 'Failed to fetch Monte Carlo results');
        } else {
          setError('Network error or server unreachable');
        }
      }
    };

    fetchResults();
  }, [simulationId]);

  // Format numbers for display
  const formatNumber = (value, decimals = 2, prefix = '') => {
    if (value === undefined || value === null) return '-';
    return `${prefix}${Number(value).toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })}`;
  };

  // Format percentages for display
  const formatPercentage = (value, decimals = 2) => {
    if (value === undefined || value === null) return '-';
    return `${formatNumber(value * 100, decimals)}%`;
  };

  // Format currency values
  const formatCurrency = (value, decimals = 2) => {
    if (value === undefined || value === null) return '-';
    return formatNumber(value, decimals, '$');
  };

  // Prepare equity curves chart configuration
  const getEquityCurvesConfig = () => {
    if (!results || !results.equity_curves) return null;

    const timestamps = results.equity_curves.median.map(point => point.timestamp);
    
    const series = [
      {
        name: 'Median',
        data: results.equity_curves.median.map(point => point.equity)
      }
    ];

    // Add percentile curves if available
    if (results.equity_curves.percentile_5) {
      series.push({
        name: '5th Percentile',
        data: results.equity_curves.percentile_5.map(point => point.equity)
      });
    }
    if (results.equity_curves.percentile_25) {
      series.push({
        name: '25th Percentile',
        data: results.equity_curves.percentile_25.map(point => point.equity)
      });
    }
    if (results.equity_curves.percentile_75) {
      series.push({
        name: '75th Percentile',
        data: results.equity_curves.percentile_75.map(point => point.equity)
      });
    }
    if (results.equity_curves.percentile_95) {
      series.push({
        name: '95th Percentile',
        data: results.equity_curves.percentile_95.map(point => point.equity)
      });
    }

    return {
      series,
      options: {
        chart: {
          type: 'line',
          height: 350,
          toolbar: {
            show: true
          }
        },
        stroke: {
          curve: 'smooth',
          width: [4, 1, 1, 1, 1]
        },
        colors: ['#2E93fA', '#99c1f1', '#b3d1f5', '#66adf1', '#0062cc'],
        xaxis: {
          type: 'datetime',
          categories: timestamps,
          labels: {
            datetimeFormatter: {
              year: 'yyyy',
              month: 'MMM \'yy',
              day: 'dd MMM',
              hour: 'HH:mm'
            }
          }
        },
        yaxis: {
          title: {
            text: 'Account Balance'
          },
          labels: {
            formatter: (value) => formatCurrency(value, 2)
          }
        },
        tooltip: {
          shared: true,
          intersect: false,
          y: {
            formatter: (value) => formatCurrency(value, 2)
          }
        },
        legend: {
          position: 'top'
        },
        title: {
          text: 'Equity Curves Across Simulations',
          align: 'left'
        }
      }
    };
  };

  // Prepare final balance distribution chart
  const getBalanceDistributionConfig = () => {
    if (!results || !results.percentiles || !results.percentiles.final_balance) return null;
    
    // Calculate distribution buckets from percentiles
    const min = results.summary.min_final_balance;
    const max = results.summary.max_final_balance;
    
    // We'll use the percentiles to create a histogram-like chart
    const balances = Object.values(results.percentiles.final_balance);
    
    return {
      series: [{
        name: 'Final Balance Distribution',
        data: balances
      }],
      options: {
        chart: {
          type: 'bar',
          height: 350
        },
        plotOptions: {
          bar: {
            borderRadius: 4,
            dataLabels: {
              position: 'top'
            }
          }
        },
        dataLabels: {
          enabled: true,
          formatter: (val) => formatCurrency(val),
          offsetY: -20,
          style: {
            fontSize: '12px',
            colors: ["#304758"]
          }
        },
        xaxis: {
          categories: Object.keys(results.percentiles.final_balance).map(key => `${key}%`),
          position: 'bottom',
          title: {
            text: 'Percentile'
          }
        },
        yaxis: {
          title: {
            text: 'Account Balance'
          },
          labels: {
            formatter: (value) => formatCurrency(value, 0)
          }
        },
        title: {
          text: 'Final Balance Distribution',
          align: 'left'
        },
        subtitle: {
          text: `Range: ${formatCurrency(min)} to ${formatCurrency(max)}`,
          align: 'left'
        },
        colors: ['#2E93fA']
      }
    };
  };

  // Render loading state
  if (isLoading) {
    return (
      <Card variant="outlined">
        <CardContent>
          <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" p={4}>
            <CircularProgress size={40} />
            <Typography variant="body1" sx={{ mt: 2 }}>
              Loading Monte Carlo simulation results...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  // Render error state
  if (error) {
    return (
      <Card variant="outlined">
        <CardContent>
          <Alert severity="error">
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  // Render no results state
  if (!results) {
    return (
      <Card variant="outlined">
        <CardContent>
          <Alert severity="info">
            No Monte Carlo simulation results available. Please run a simulation first.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  // Get chart configs
  const equityCurvesConfig = getEquityCurvesConfig();
  const balanceDistributionConfig = getBalanceDistributionConfig();

  // Prepare risk metrics color based on value
  const getRiskColor = (value, type) => {
    if (type === 'profit_probability') {
      if (value > 0.7) return 'success.main';
      if (value > 0.5) return 'warning.main';
      return 'error.main';
    }
    
    if (type === 'loss_probability' || type.includes('var') || type.includes('drawdown')) {
      if (value < 0.1) return 'success.main';
      if (value < 0.3) return 'warning.main';
      return 'error.main';
    }
    
    return 'text.primary';
  };

  return (
    <Card variant="outlined">
      <CardHeader 
        title="Monte Carlo Simulation Results" 
        subheader={`${results.simulations} simulations analyzed`}
      />
      <CardContent>
        <Grid container spacing={3}>
          {/* Summary Statistics */}
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Summary Statistics
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Average Final Balance</TableCell>
                      <TableCell align="right">{formatCurrency(results.summary.avg_final_balance)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Median Final Balance</TableCell>
                      <TableCell align="right">{formatCurrency(results.summary.median_final_balance)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Best Case Balance</TableCell>
                      <TableCell align="right" sx={{ color: 'success.main' }}>
                        {formatCurrency(results.summary.max_final_balance)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Worst Case Balance</TableCell>
                      <TableCell align="right" sx={{ color: 'error.main' }}>
                        {formatCurrency(results.summary.min_final_balance)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Standard Deviation</TableCell>
                      <TableCell align="right">{formatCurrency(results.summary.std_dev_balance)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Profit Probability</TableCell>
                      <TableCell 
                        align="right" 
                        sx={{ color: getRiskColor(results.summary.profit_probability, 'profit_probability') }}
                      >
                        {formatPercentage(results.summary.profit_probability)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Loss Probability</TableCell>
                      <TableCell 
                        align="right" 
                        sx={{ color: getRiskColor(results.summary.loss_probability, 'loss_probability') }}
                      >
                        {formatPercentage(results.summary.loss_probability)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          {/* Risk Metrics */}
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Risk Metrics
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>
                        <Tooltip title="Value at Risk (95% confidence level): The minimum expected loss in the worst 5% of scenarios">
                          <span>Value at Risk (95%)</span>
                        </Tooltip>
                      </TableCell>
                      <TableCell align="right" sx={{ color: getRiskColor(results.risk_metrics.var_95, 'var_95') }}>
                        {formatCurrency(results.risk_metrics.var_95)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Tooltip title="Value at Risk (99% confidence level): The minimum expected loss in the worst 1% of scenarios">
                          <span>Value at Risk (99%)</span>
                        </Tooltip>
                      </TableCell>
                      <TableCell align="right" sx={{ color: getRiskColor(results.risk_metrics.var_99, 'var_99') }}>
                        {formatCurrency(results.risk_metrics.var_99)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Tooltip title="Conditional Value at Risk (95% confidence level): The average loss in the worst 5% of scenarios">
                          <span>CVaR (95%)</span>
                        </Tooltip>
                      </TableCell>
                      <TableCell align="right" sx={{ color: getRiskColor(results.risk_metrics.cvar_95, 'cvar_95') }}>
                        {formatCurrency(results.risk_metrics.cvar_95)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Tooltip title="Conditional Value at Risk (99% confidence level): The average loss in the worst 1% of scenarios">
                          <span>CVaR (99%)</span>
                        </Tooltip>
                      </TableCell>
                      <TableCell align="right" sx={{ color: getRiskColor(results.risk_metrics.cvar_99, 'cvar_99') }}>
                        {formatCurrency(results.risk_metrics.cvar_99)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Maximum Drawdown (Mean)</TableCell>
                      <TableCell align="right" sx={{ color: getRiskColor(results.risk_metrics.max_drawdown_mean, 'max_drawdown') }}>
                        {formatPercentage(results.risk_metrics.max_drawdown_mean / 100)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Maximum Drawdown (Median)</TableCell>
                      <TableCell align="right" sx={{ color: getRiskColor(results.risk_metrics.max_drawdown_median, 'max_drawdown') }}>
                        {formatPercentage(results.risk_metrics.max_drawdown_median / 100)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Maximum Drawdown (Worst)</TableCell>
                      <TableCell align="right" sx={{ color: getRiskColor(results.risk_metrics.max_drawdown_worst, 'max_drawdown_worst') }}>
                        {formatPercentage(results.risk_metrics.max_drawdown_worst / 100)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          {/* Equity Curves Chart */}
          <Grid item xs={12}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              {equityCurvesConfig ? (
                <Chart
                  ref={equityCurvesChartRef}
                  options={equityCurvesConfig.options}
                  series={equityCurvesConfig.series}
                  type="line"
                  height={350}
                />
              ) : (
                <Box display="flex" justifyContent="center" alignItems="center" height={350}>
                  <Typography color="textSecondary">Equity curve data not available</Typography>
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Balance Distribution Chart */}
          <Grid item xs={12}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              {balanceDistributionConfig ? (
                <Chart
                  ref={balanceDistributionChartRef}
                  options={balanceDistributionConfig.options}
                  series={balanceDistributionConfig.series}
                  type="bar"
                  height={350}
                />
              ) : (
                <Box display="flex" justifyContent="center" alignItems="center" height={350}>
                  <Typography color="textSecondary">Balance distribution data not available</Typography>
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Interpretation and Recommendations */}
          <Grid item xs={12}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Interpretation & Recommendations
              </Typography>
              <Divider sx={{ my: 1 }} />
              
              <Box my={2}>
                <Typography variant="subtitle1" gutterBottom>
                  Strategy Robustness
                </Typography>
                <Typography variant="body2" paragraph>
                  {results.summary.profit_probability > 0.7 
                    ? "Your strategy shows good robustness with a high probability of profit across different trade sequences."
                    : results.summary.profit_probability > 0.5
                    ? "Your strategy shows moderate robustness. Consider improving your risk management to increase consistency."
                    : "Your strategy shows low robustness, with profit probability below 50%. Consider revising your trading rules or risk management."
                  }
                </Typography>
              </Box>
              
              <Box my={2}>
                <Typography variant="subtitle1" gutterBottom>
                  Risk Assessment
                </Typography>
                <Typography variant="body2" paragraph>
                  The maximum drawdown across simulations ranges from 
                  {` ${formatPercentage(results.risk_metrics.max_drawdown_mean / 100)} `}
                  (average) to 
                  {` ${formatPercentage(results.risk_metrics.max_drawdown_worst / 100)} `}
                  (worst case). 
                  {results.risk_metrics.max_drawdown_worst > 40
                    ? " This drawdown level is quite high and might be psychologically difficult to endure."
                    : results.risk_metrics.max_drawdown_worst > 25
                    ? " This drawdown level is moderate but might be challenging during extended losing periods."
                    : " This drawdown level is relatively low, suggesting good risk control."
                  }
                </Typography>
              </Box>
              
              <Box my={2}>
                <Typography variant="subtitle1" gutterBottom>
                  Position Sizing Recommendation
                </Typography>
                <Typography variant="body2" paragraph>
                  Based on Value-at-Risk metrics, you should consider limiting position sizes to avoid losing more than 
                  {` ${formatPercentage(results.risk_metrics.var_95 / results.summary.avg_final_balance)} `}
                  of your capital in adverse scenarios.
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

export default MonteCarloResults; 