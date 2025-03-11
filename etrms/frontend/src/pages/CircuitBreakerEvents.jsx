import React, { useState, useEffect } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from '@mui/material';
import {
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { api } from '../services/api';
import PageHeader from '../components/PageHeader';

const CircuitBreakerEvents = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [events, setEvents] = useState([]);
  const [circuitBreakers, setCircuitBreakers] = useState([]);
  const [selectedBreaker, setSelectedBreaker] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalCount, setTotalCount] = useState(0);

  // Fetch circuit breakers on mount
  useEffect(() => {
    const fetchCircuitBreakers = async () => {
      try {
        const response = await api.getCircuitBreakers();
        setCircuitBreakers(response);
      } catch (err) {
        console.error('Error fetching circuit breakers:', err);
        setError('Failed to load circuit breakers. Please try again later.');
      }
    };

    fetchCircuitBreakers();
  }, []);

  // Fetch events when page, rowsPerPage, or selectedBreaker changes
  useEffect(() => {
    const fetchEvents = async () => {
      setLoading(true);
      setError(null);

      try {
        let response;
        if (selectedBreaker === 'all') {
          response = await api.getAllCircuitBreakerEvents(rowsPerPage, page * rowsPerPage);
        } else {
          response = await api.getCircuitBreakerEvents(selectedBreaker, rowsPerPage, page * rowsPerPage);
        }

        setEvents(response.events);
        setTotalCount(response.total);
      } catch (err) {
        console.error('Error fetching circuit breaker events:', err);
        setError('Failed to load events. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [page, rowsPerPage, selectedBreaker]);

  // Handle circuit breaker selection change
  const handleBreakerChange = (event) => {
    setSelectedBreaker(event.target.value);
    setPage(0); // Reset to first page when changing filter
  };

  // Handle page change
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  // Handle rows per page change
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Get severity chip for event type
  const getSeverityChip = (eventType) => {
    switch (eventType) {
      case 'TRIGGERED':
        return <Chip icon={<WarningIcon />} label="Triggered" color="warning" />;
      case 'RESOLVED':
        return <Chip icon={<CheckCircleIcon />} label="Resolved" color="success" />;
      case 'ERROR':
        return <Chip icon={<ErrorIcon />} label="Error" color="error" />;
      default:
        return <Chip icon={<InfoIcon />} label={eventType} color="info" />;
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy HH:mm:ss');
    } catch (err) {
      return dateString;
    }
  };

  return (
    <Container maxWidth="lg">
      <PageHeader
        title="Circuit Breaker Events"
        description="View history of circuit breaker triggers and actions"
      />

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      <Card sx={{ mb: 4 }}>
        <CardHeader title="Event Filters" />
        <Divider />
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Circuit Breaker</InputLabel>
                <Select
                  value={selectedBreaker}
                  onChange={handleBreakerChange}
                  label="Circuit Breaker"
                >
                  <MenuItem value="all">All Circuit Breakers</MenuItem>
                  {circuitBreakers.map((breaker) => (
                    <MenuItem key={breaker.id} value={breaker.id}>
                      {breaker.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title="Event History" />
        <Divider />
        <CardContent>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : events.length === 0 ? (
            <Typography variant="body1" color="textSecondary" align="center">
              No events found
            </Typography>
          ) : (
            <>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Circuit Breaker</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Condition</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell>Details</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {events.map((event) => (
                      <TableRow key={event.id}>
                        <TableCell>{formatDate(event.timestamp)}</TableCell>
                        <TableCell>{event.circuit_breaker_name}</TableCell>
                        <TableCell>{getSeverityChip(event.event_type)}</TableCell>
                        <TableCell>{event.condition_description}</TableCell>
                        <TableCell>{event.action_taken}</TableCell>
                        <TableCell>
                          <Typography variant="body2" component="div">
                            {event.details}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                component="div"
                count={totalCount}
                page={page}
                onPageChange={handleChangePage}
                rowsPerPage={rowsPerPage}
                onRowsPerPageChange={handleChangeRowsPerPage}
                rowsPerPageOptions={[5, 10, 25, 50]}
              />
            </>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

export default CircuitBreakerEvents; 