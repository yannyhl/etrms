import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Tab,
  Tabs,
  Typography,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
} from '@mui/icons-material';

import { RiskDashboard } from '../components/RiskDashboard';
import CircuitBreakerForm from '../components/CircuitBreakerForm';
import PageHeader from '../components/PageHeader';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`risk-tabpanel-${index}`}
      aria-labelledby={`risk-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index) {
  return {
    id: `risk-tab-${index}`,
    'aria-controls': `risk-tabpanel-${index}`,
  };
}

export const RiskManagement = () => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="xl">
      <PageHeader
        title="Risk Management"
        description="Monitor and control risk across all connected exchanges."
      />

      <Paper sx={{ mb: 4 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="risk management tabs"
          variant="fullWidth"
        >
          <Tab
            label="Dashboard"
            icon={<DashboardIcon />}
            iconPosition="start"
            {...a11yProps(0)}
          />
          <Tab
            label="Circuit Breakers"
            icon={<SettingsIcon />}
            iconPosition="start"
            {...a11yProps(1)}
          />
          <Tab
            label="Event History"
            icon={<HistoryIcon />}
            iconPosition="start"
            {...a11yProps(2)}
          />
        </Tabs>
      </Paper>

      <TabPanel value={activeTab} index={0}>
        <RiskDashboard />
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <CircuitBreakerForm />
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Risk Event History
          </Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            This panel will show a history of risk events, including circuit breaker triggers,
            significant drawdowns, and other important risk-related events.
          </Typography>
          <Paper sx={{ p: 3, backgroundColor: 'action.hover' }}>
            <Typography variant="body1" align="center">
              Event history functionality will be implemented in a future update.
            </Typography>
          </Paper>
        </Box>
      </TabPanel>
    </Container>
  );
};

export default RiskManagement; 