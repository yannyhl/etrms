/**
 * Application configuration
 */

// API configuration
export const API_BASE_URL = 'http://localhost:8000';

// Backtesting configuration
export const BACKTEST_TYPES = [
  { value: 'standard', label: 'Standard Backtest' },
  { value: 'monte_carlo', label: 'Monte Carlo Simulation' },
  { value: 'walk_forward', label: 'Walk-Forward Analysis' },
  { value: 'optimization', label: 'Parameter Optimization' }
];

export const TIMEFRAMES = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '30m', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' }
];

export const EXCHANGES = [
  { value: 'binance', label: 'Binance' },
  { value: 'hyperliquid', label: 'Hyperliquid' },
  { value: 'bybit', label: 'Bybit' }
];

// Chart configuration
export const CHART_COLORS = {
  primary: '#0ea5e9',
  secondary: '#6366f1',
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
  light: '#f3f4f6',
  dark: '#1f2937'
};

// Default chart options
export const DEFAULT_CHART_OPTIONS = {
  chart: {
    toolbar: {
      show: true,
      tools: {
        download: true,
        selection: true,
        zoom: true,
        zoomin: true,
        zoomout: true,
        pan: true,
        reset: true
      }
    },
    animations: {
      enabled: true,
      easing: 'easeinout',
      speed: 800,
      animateGradually: {
        enabled: true,
        delay: 150
      },
      dynamicAnimation: {
        enabled: true,
        speed: 350
      }
    }
  },
  colors: [
    CHART_COLORS.primary,
    CHART_COLORS.secondary,
    CHART_COLORS.success,
    CHART_COLORS.warning,
    CHART_COLORS.danger
  ],
  stroke: {
    curve: 'smooth',
    width: 2
  },
  tooltip: {
    theme: 'dark',
    shared: true
  },
  grid: {
    borderColor: '#374151',
    strokeDashArray: 4,
    xaxis: {
      lines: {
        show: true
      }
    }
  },
  xaxis: {
    labels: {
      style: {
        colors: '#9ca3af'
      }
    }
  },
  yaxis: {
    labels: {
      style: {
        colors: '#9ca3af'
      }
    }
  }
}; 