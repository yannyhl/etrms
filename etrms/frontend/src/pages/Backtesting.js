import React, { useState, useEffect } from 'react';
import { Tab } from '@headlessui/react';
import axios from 'axios';
import { ChartBarIcon, CogIcon, ArrowPathIcon, ChartPieIcon, BeakerIcon } from '@heroicons/react/24/outline';
import { API_BASE_URL } from '../config';

// Import custom components that we'll create
import BasicBacktestForm from '../components/backtesting/BasicBacktestForm';
import BacktestResults from '../components/backtesting/BacktestResults';
import ParameterOptimizationForm from '../components/backtesting/ParameterOptimizationForm';
import OptimizationResults from '../components/backtesting/OptimizationResults';
import WalkForwardForm from '../components/backtesting/WalkForwardForm';
import WalkForwardResults from '../components/backtesting/WalkForwardResults';
import MonteCarloForm from '../components/backtesting/MonteCarloForm';
import MonteCarloResults from '../components/backtesting/MonteCarloResults';
import TasksList from '../components/backtesting/TasksList';

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
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

  // Fetch backtesting tasks when component mounts
  useEffect(() => {
    fetchTasks();
    fetchStrategies();
  }, []);

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('/api/v1/backtesting/tasks');
      setTasks(response.data.tasks || []);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setError('Failed to fetch backtesting tasks. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStrategies = async () => {
    try {
      const response = await axios.get('/api/v1/backtesting/available-strategies');
      setAvailableStrategies(response.data || []);
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
    console.log('Monte Carlo simulation completed:', simulationData);
    setMonteCarloSimulationId(simulationData.monte_carlo_id);
  };

  const tabs = [
    { name: 'Backtests', icon: ChartBarIcon },
    { name: 'Parameter Optimization', icon: CogIcon },
    { name: 'Walk-Forward Analysis', icon: ArrowPathIcon },
    { name: 'Monte Carlo', icon: ChartPieIcon },
    { name: 'Tasks', icon: BeakerIcon }
  ];

  return (
    <div className="py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Backtesting</h1>
        <p className="mt-2 text-sm text-gray-700">
          Test and optimize your trading strategies with historical data
        </p>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Tab.Group selectedIndex={selectedTabIndex} onChange={setSelectedTabIndex}>
          <Tab.List className="flex p-1 space-x-1 bg-gray-100 rounded-t-lg">
            {tabs.map((tab) => (
              <Tab
                key={tab.name}
                className={({ selected }) =>
                  classNames(
                    'w-full py-3 px-4 text-sm font-medium rounded-md flex items-center justify-center',
                    'focus:outline-none focus:ring-2 ring-offset-2 ring-offset-blue-400 ring-blue-500',
                    selected
                      ? 'bg-white text-blue-600 shadow'
                      : 'text-gray-700 hover:bg-gray-200 hover:text-gray-900'
                  )
                }
              >
                <tab.icon className="mr-2 h-5 w-5" />
                {tab.name}
              </Tab>
            ))}
          </Tab.List>
          <Tab.Panels className="p-4">
            {/* Backtest Tab */}
            <Tab.Panel>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h2 className="text-lg font-medium mb-4">Configure Backtest</h2>
                  <BasicBacktestForm 
                    strategies={availableStrategies} 
                    onTaskCreated={handleTaskCreated} 
                  />
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h2 className="text-lg font-medium mb-4">Backtest Results</h2>
                  <BacktestResults selectedTask={selectedTask} />
                </div>
              </div>
            </Tab.Panel>

            {/* Parameter Optimization Tab */}
            <Tab.Panel>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h2 className="text-lg font-medium mb-4">Configure Optimization</h2>
                  <ParameterOptimizationForm 
                    strategies={availableStrategies} 
                    onTaskCreated={handleTaskCreated} 
                  />
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h2 className="text-lg font-medium mb-4">Optimization Results</h2>
                  <OptimizationResults selectedTask={selectedTask} />
                </div>
              </div>
            </Tab.Panel>

            {/* Walk-Forward Analysis Tab */}
            <Tab.Panel>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h2 className="text-lg font-medium mb-4">Configure Walk-Forward Analysis</h2>
                  <WalkForwardForm 
                    strategies={availableStrategies} 
                    onTaskCreated={handleTaskCreated} 
                  />
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h2 className="text-lg font-medium mb-4">Walk-Forward Results</h2>
                  <WalkForwardResults selectedTask={selectedTask} />
                </div>
              </div>
            </Tab.Panel>

            {/* Monte Carlo Tab */}
            <Tab.Panel>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h2 className="text-lg font-medium mb-4">Configure Monte Carlo Simulation</h2>
                  <MonteCarloForm 
                    tasks={tasks} 
                    onTaskCreated={handleTaskCreated} 
                  />
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h2 className="text-lg font-medium mb-4">Monte Carlo Results</h2>
                  <MonteCarloResults selectedTask={selectedTask} />
                </div>
              </div>
            </Tab.Panel>

            {/* Tasks Tab */}
            <Tab.Panel>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h2 className="text-lg font-medium mb-4">Backtesting Tasks</h2>
                <TasksList 
                  tasks={tasks} 
                  isLoading={isLoading} 
                  error={error} 
                  onTaskSelect={handleTaskSelect} 
                  onTasksRefresh={fetchTasks} 
                />
              </div>
            </Tab.Panel>
          </Tab.Panels>
        </Tab.Group>
      </div>
    </div>
  );
}

export default Backtesting; 