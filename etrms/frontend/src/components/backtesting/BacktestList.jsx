import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Cancel as CancelIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { api } from '../../services/api';
import { handleApiError } from '../../utils/errorHandler';
import { useAlert } from '../../hooks/useAlert';
import AlertMessage from '../AlertMessage';

/**
 * Component to display a list of backtests
 * 
 * @param {Object} props - Component props
 * @param {Function} props.onBacktestSelect - Function to call when a backtest is selected
 * @returns {React.ReactElement} The BacktestList component
 */
const BacktestList = ({ onBacktestSelect }) => {
  const [backtests, setBacktests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [backtestToDelete, setBacktestToDelete] = useState(null);
  const { alert, showSuccess, showError, closeAlert } = useAlert();

  // Fetch backtests on component mount and when page or rowsPerPage changes
  useEffect(() => {
    fetchBacktests();
  }, [page, rowsPerPage]);

  // Fetch backtests from the API
  const fetchBacktests = async () => {
    setLoading(true);
    try {
      const response = await api.get('/backtest', {
        params: {
          skip: page * rowsPerPage,
          limit: rowsPerPage,
        },
      });
      setBacktests(response.data.backtests);
      setTotalCount(response.data.total);
    } catch (error) {
      handleApiError(error, 'BacktestList.fetchBacktests', showError);
    } finally {
      setLoading(false);
    }
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

  // Handle delete button click
  const handleDeleteClick = (backtest) => {
    setBacktestToDelete(backtest);
    setDeleteDialogOpen(true);
  };

  // Handle delete confirmation
  const handleDeleteConfirm = async () => {
    if (!backtestToDelete) return;

    setLoading(true);
    try {
      await api.delete(`/backtest/${backtestToDelete.id}`);
      showSuccess('Backtest deleted successfully');
      fetchBacktests();
    } catch (error) {
      handleApiError(error, 'BacktestList.handleDeleteConfirm', showError);
    } finally {
      setLoading(false);
      setDeleteDialogOpen(false);
      setBacktestToDelete(null);
    }
  };

  // Handle cancel button click
  const handleCancelClick = async (backtest) => {
    setLoading(true);
    try {
      await api.post(`/backtest/${backtest.id}/cancel`);
      showSuccess('Backtest cancelled successfully');
      fetchBacktests();
    } catch (error) {
      handleApiError(error, 'BacktestList.handleCancelClick', showError);
    } finally {
      setLoading(false);
    }
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

  // Format date for display
  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy HH:mm:ss');
    } catch (err) {
      return dateString;
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" component="h2">
            Backtest History
          </Typography>
          <Button
            variant="outlined"
            color="primary"
            onClick={fetchBacktests}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        <AlertMessage
          open={alert.open}
          type={alert.type}
          message={alert.message}
          onClose={closeAlert}
        />

        {loading && backtests.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : backtests.length === 0 ? (
          <Typography variant="body1" color="textSecondary" align="center">
            No backtests found. Create a new backtest to get started.
          </Typography>
        ) : (
          <>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Date Range</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {backtests.map((backtest) => (
                    <TableRow key={backtest.id}>
                      <TableCell>{backtest.name}</TableCell>
                      <TableCell>{backtest.type}</TableCell>
                      <TableCell>
                        {formatDate(backtest.start_date)} - {formatDate(backtest.end_date)}
                      </TableCell>
                      <TableCell>{getStatusChip(backtest.status)}</TableCell>
                      <TableCell>{formatDate(backtest.created_at)}</TableCell>
                      <TableCell>
                        <IconButton
                          color="primary"
                          onClick={() => onBacktestSelect(backtest.id)}
                          title="View Results"
                        >
                          <VisibilityIcon />
                        </IconButton>
                        {backtest.status === 'running' && (
                          <IconButton
                            color="warning"
                            onClick={() => handleCancelClick(backtest)}
                            title="Cancel Backtest"
                          >
                            <CancelIcon />
                          </IconButton>
                        )}
                        {backtest.status === 'failed' && (
                          <IconButton
                            color="primary"
                            onClick={() => {
                              // TODO: Implement retry functionality
                              showError('Retry functionality not implemented yet');
                            }}
                            title="Retry Backtest"
                          >
                            <PlayArrowIcon />
                          </IconButton>
                        )}
                        {backtest.status !== 'running' && (
                          <IconButton
                            color="error"
                            onClick={() => handleDeleteClick(backtest)}
                            title="Delete Backtest"
                          >
                            <DeleteIcon />
                          </IconButton>
                        )}
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

        {/* Delete Confirmation Dialog */}
        <Dialog
          open={deleteDialogOpen}
          onClose={() => setDeleteDialogOpen(false)}
        >
          <DialogTitle>Delete Backtest</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Are you sure you want to delete the backtest "{backtestToDelete?.name}"? This action cannot be undone.
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialogOpen(false)} color="primary">
              Cancel
            </Button>
            <Button onClick={handleDeleteConfirm} color="error">
              Delete
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

BacktestList.propTypes = {
  onBacktestSelect: PropTypes.func.isRequired,
};

export default BacktestList; 