import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  IconButton, 
  Chip, 
  Button, 
  CircularProgress,
  Tooltip
} from '@mui/material';
import { 
  PlayArrow as PlayIcon, 
  Delete as DeleteIcon, 
  Visibility as VisibilityIcon, 
  Refresh as RefreshIcon,
  BarChart as BarChartIcon,
  Settings as SettingsIcon,
  CompareArrows as CompareArrowsIcon,
  PieChart as PieChartIcon
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';

function TasksList({ tasks, onTaskSelect, onTasksRefresh }) {
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [loadingTaskId, setLoadingTaskId] = useState(null);
  
  const { post, del } = useApi();

  const getTaskTypeIcon = (type) => {
    switch (type) {
      case 'backtest':
        return <BarChartIcon color="primary" />;
      case 'optimization':
        return <SettingsIcon color="success" />;
      case 'walk_forward':
        return <CompareArrowsIcon color="secondary" />;
      case 'monte_carlo':
        return <PieChartIcon color="warning" />;
      default:
        return <BarChartIcon color="action" />;
    }
  };

  const getStatusChip = (status) => {
    let color;
    let label = status;
    
    switch (status) {
      case 'completed':
        color = 'success';
        break;
      case 'running':
        color = 'primary';
        break;
      case 'pending':
        color = 'default';
        break;
      case 'failed':
        color = 'error';
        break;
      case 'cancelled':
        color = 'warning';
        break;
      default:
        color = 'default';
    }
    
    return (
      <Chip 
        label={label} 
        color={color} 
        size="small" 
        variant={status === 'running' ? 'outlined' : 'filled'}
      />
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const handleViewTask = (task) => {
    setSelectedTaskId(task.id);
    onTaskSelect(task);
  };

  const handleRunTask = async (taskId) => {
    try {
      setActionLoading(true);
      setLoadingTaskId(taskId);
      
      const response = await post(`/api/v1/backtest/tasks/${taskId}/run`);
      
      if (response.status === 'success') {
        onTasksRefresh();
      }
    } catch (err) {
      console.error('Error running task:', err);
    } finally {
      setActionLoading(false);
      setLoadingTaskId(null);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!window.confirm('Are you sure you want to delete this task?')) {
      return;
    }
    
    try {
      setActionLoading(true);
      setLoadingTaskId(taskId);
      
      const response = await del(`/api/v1/backtest/tasks/${taskId}`);
      
      if (response.status === 'success') {
        onTasksRefresh();
        if (selectedTaskId === taskId) {
          setSelectedTaskId(null);
          onTaskSelect(null);
        }
      }
    } catch (err) {
      console.error('Error deleting task:', err);
    } finally {
      setActionLoading(false);
      setLoadingTaskId(null);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          {tasks.length} {tasks.length === 1 ? 'Task' : 'Tasks'}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={onTasksRefresh}
        >
          Refresh
        </Button>
      </Box>
      
      {tasks.length === 0 ? (
        <Typography variant="body1" color="textSecondary" sx={{ py: 4, textAlign: 'center' }}>
          No backtesting tasks found. Create a new backtest to get started.
        </Typography>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Exchange</TableCell>
                <TableCell>Symbol</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.map((task) => (
                <TableRow 
                  key={task.id}
                  selected={selectedTaskId === task.id}
                  hover
                  onClick={() => handleViewTask(task)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {getTaskTypeIcon(task.type)}
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {task.type}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{task.name}</TableCell>
                  <TableCell>{task.exchange}</TableCell>
                  <TableCell>{task.symbol}</TableCell>
                  <TableCell>{getStatusChip(task.status)}</TableCell>
                  <TableCell>{formatDate(task.created_at)}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex' }}>
                      <Tooltip title="View">
                        <IconButton 
                          size="small" 
                          color="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewTask(task);
                          }}
                        >
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      
                      <Tooltip title="Run">
                        <IconButton 
                          size="small" 
                          color="success"
                          disabled={task.status === 'running' || (actionLoading && loadingTaskId === task.id)}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRunTask(task.id);
                          }}
                        >
                          {actionLoading && loadingTaskId === task.id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <PlayIcon fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>
                      
                      <Tooltip title="Delete">
                        <IconButton 
                          size="small" 
                          color="error"
                          disabled={actionLoading && loadingTaskId === task.id}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteTask(task.id);
                          }}
                        >
                          {actionLoading && loadingTaskId === task.id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <DeleteIcon fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export default TasksList; 