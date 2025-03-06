import React, { useState } from 'react';
import axios from 'axios';
import { 
  PlayIcon, 
  TrashIcon, 
  EyeIcon, 
  ArrowPathIcon,
  ChartBarIcon,
  CogIcon,
  ArrowsRightLeftIcon,
  ChartPieIcon
} from '@heroicons/react/24/outline';

function TasksList({ tasks, isLoading, error, onTaskSelect, onTasksRefresh }) {
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const getTaskTypeIcon = (type) => {
    switch (type) {
      case 'backtest':
        return <ChartBarIcon className="h-5 w-5 text-blue-500" />;
      case 'optimization':
        return <CogIcon className="h-5 w-5 text-green-500" />;
      case 'walk_forward':
        return <ArrowsRightLeftIcon className="h-5 w-5 text-purple-500" />;
      case 'monte_carlo':
        return <ChartPieIcon className="h-5 w-5 text-orange-500" />;
      default:
        return <ChartBarIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    let bgColor, textColor, label;

    switch (status) {
      case 'pending':
        bgColor = 'bg-yellow-100';
        textColor = 'text-yellow-800';
        label = 'Pending';
        break;
      case 'running':
        bgColor = 'bg-blue-100';
        textColor = 'text-blue-800';
        label = 'Running';
        break;
      case 'completed':
        bgColor = 'bg-green-100';
        textColor = 'text-green-800';
        label = 'Completed';
        break;
      case 'failed':
        bgColor = 'bg-red-100';
        textColor = 'text-red-800';
        label = 'Failed';
        break;
      default:
        bgColor = 'bg-gray-100';
        textColor = 'text-gray-800';
        label = status || 'Unknown';
    }

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${bgColor} ${textColor}`}>
        {label}
      </span>
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
    setActionLoading(true);
    try {
      await axios.post(`/api/v1/backtesting/run`, { task_id: taskId });
      onTasksRefresh();
    } catch (err) {
      console.error('Error running task:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!window.confirm('Are you sure you want to delete this task and all associated results?')) {
      return;
    }
    
    setActionLoading(true);
    try {
      await axios.delete(`/api/v1/backtesting/tasks/${taskId}`);
      if (selectedTaskId === taskId) {
        setSelectedTaskId(null);
        onTaskSelect(null);
      }
      onTasksRefresh();
    } catch (err) {
      console.error('Error deleting task:', err);
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading) {
    return <div className="flex justify-center py-6">Loading tasks...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">{error}</h3>
          </div>
        </div>
      </div>
    );
  }

  if (!tasks || tasks.length === 0) {
    return (
      <div className="text-center py-6 text-gray-500">
        No backtesting tasks found. Create a new task to begin.
        <div className="mt-4">
          <button
            onClick={onTasksRefresh}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <ArrowPathIcon className="h-5 w-5 mr-2" />
            Refresh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
          <div className="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Strategy
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tasks.map((task) => (
                  <tr 
                    key={task.id} 
                    className={selectedTaskId === task.id ? 'bg-blue-50' : 'hover:bg-gray-50'}
                    onClick={() => handleViewTask(task)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getTaskTypeIcon(task.task_type)}
                        <span className="ml-2 text-sm text-gray-900 capitalize">
                          {task.task_type?.replace('_', ' ') || 'Unknown'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{task.name || 'N/A'}</div>
                      <div className="text-sm text-gray-500">{task.symbols?.join(', ') || 'N/A'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{task.strategy_name || 'N/A'}</div>
                      <div className="text-sm text-gray-500">
                        {task.timeframe || 'N/A'} | {formatDate(task.start_date)} - {formatDate(task.end_date)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(task.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(task.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewTask(task);
                          }}
                          className="text-blue-600 hover:text-blue-900"
                          title="View results"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                        {task.status !== 'running' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRunTask(task.id);
                            }}
                            disabled={actionLoading}
                            className="text-green-600 hover:text-green-900 disabled:text-gray-400"
                            title="Run backtest"
                          >
                            <PlayIcon className="h-5 w-5" />
                          </button>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteTask(task.id);
                          }}
                          disabled={actionLoading}
                          className="text-red-600 hover:text-red-900 disabled:text-gray-400"
                          title="Delete task"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div className="mt-4 flex justify-end">
        <button
          onClick={onTasksRefresh}
          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <ArrowPathIcon className="h-5 w-5 mr-2" />
          Refresh
        </button>
      </div>
    </div>
  );
}

export default TasksList; 