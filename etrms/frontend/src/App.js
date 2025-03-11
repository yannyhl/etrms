import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Positions from './pages/Positions';
import Accounts from './pages/Accounts';
import RiskManagement from './pages/RiskManagement';
import Configuration from './pages/Configuration';
import AIAssistant from './pages/AIAssistant';
import Backtesting from './pages/Backtesting';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import TestPage from './pages/TestPage';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Routes>
      {/* Authentication Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Test Page - No Authentication Required */}
      <Route path="/test" element={<TestPage />} />
      
      {/* Protected Routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Dashboard />} />
        <Route path="positions" element={<Positions />} />
        <Route path="accounts" element={<Accounts />} />
        <Route path="risk" element={<RiskManagement />} />
        <Route path="backtesting" element={<Backtesting />} />
        <Route path="config" element={<Configuration />} />
        <Route path="assistant" element={<AIAssistant />} />
        <Route path="profile" element={<Profile />} />
      </Route>
      
      {/* Catch-all route - redirect to dashboard */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App; 