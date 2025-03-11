# Enhanced Trading Risk Management System (ETRMS)

> **Development Status**: This project is currently under active development. The frontend UI and documentation are largely complete, but many backend components still need to be implemented. See the [Development Guide](docs/DEVELOPMENT.md) for details on what's implemented and what's still needed.

## Overview

The Enhanced Trading Risk Management System (ETRMS) is a comprehensive solution designed to provide automated risk control mechanisms for futures trading on Binance and Hyperliquid exchanges, augmented with AI-powered market analysis and trading assistance. The system combines robust circuit breakers, advanced market analytics, and institutional-grade risk management practices to optimize trading performance while minimizing downside risk.

## Core Components

1. **Risk Management Engine**: Automated circuit breakers, position monitoring, and risk threshold enforcement
2. **Market Analysis Framework**: Real-time market condition assessment, volume profile analysis, and liquidity mapping
3. **AI Trading Assistant**: Intelligent trading recommendations, setup identification, and performance analytics
4. **User Dashboard**: Unified interface for monitoring positions, analyzing market conditions, and configuring risk parameters
5. **Backtesting Engine**: Comprehensive framework for testing trading strategies and risk management configurations

## Key Features

- Multi-level circuit breakers based on position-specific and account-wide metrics
- Comprehensive market analysis including volume profiles, order book depth, and liquidity zones
- Quantitative risk management methodologies with behavioral safeguards
- AI-powered trading assistance based on institutional trading patterns
- Unified interface for monitoring and controlling all aspects of trading activity
- Advanced backtesting capabilities for strategy development and risk management optimization

## Current Development Status

### Completed Components
- Frontend UI implementation for all pages
- Project structure and architecture
- Comprehensive documentation
- API route definitions
- Backtesting module with full integration with risk management
- Exchange API integration for Binance Futures and Hyperliquid

### Components In Progress
- Data models implementation
- Core risk engine functionality
- Backend API endpoints

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for a detailed breakdown of what's implemented and what still needs work.

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 14+
- Redis 7+
- Docker and Docker Compose (for containerized deployment)

### Development Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/etrms.git
   cd etrms
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Install frontend dependencies:
   ```bash
   cd ../frontend
   npm install
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. Start the development servers:
   ```bash
   # Backend (in one terminal)
   cd backend
   uvicorn app:app --reload

   # Frontend (in another terminal)
   cd frontend
   npm run dev
   ```

### Using Docker for Development

```bash
docker-compose -f docker/docker-compose.dev.yml up
```

> **Note**: Since many backend components are still in development, the system is not yet fully functional. You can run the frontend to view the UI, but most features will not work without backend implementation.

## Contributing to Development

If you'd like to contribute to completing this project:

1. Check the [DEVELOPMENT.md](docs/DEVELOPMENT.md) file for details on what needs to be implemented
2. Focus on the components listed in the "Next Steps" section
3. Follow the project architecture and design patterns established in existing code
4. Add tests for all new components you implement

## Project Structure

The project follows a modular architecture:

```
etrms/
├── backend/               # Python FastAPI backend
├── frontend/              # React TypeScript frontend
├── database/              # Database migrations and seeds
├── docker/                # Docker configuration
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

## Documentation

For more detailed documentation, please refer to the following resources:

- [Development Guide](docs/DEVELOPMENT.md) - Technical documentation for developers
- [Usage Guide](docs/USAGE_GUIDE.md) - Comprehensive guide on using the system with real-time trading
- [API Documentation](docs/api/README.md) - Detailed API reference
- [Architecture Overview](docs/architecture/) - System architecture and design principles
- [Deployment Guide](docs/deployment/) - Instructions for production deployment

## Using ETRMS for Trading

ETRMS is designed to be used alongside your real-time trading activities. The system provides:

1. **Automated Risk Management** - Circuit breakers automatically protect your account from excessive losses
2. **Position Monitoring** - Track all positions across exchanges in a unified interface
3. **AI-Driven Insights** - Get intelligent trading recommendations and market analysis
4. **Performance Analytics** - Analyze your trading performance with detailed metrics
5. **Comprehensive Backtesting** - Test your trading strategies and risk management configurations before deploying them in live trading

### Backtesting Module

The backtesting module allows you to:

- Test trading strategies with historical data
- Evaluate the effectiveness of circuit breaker configurations
- Optimize strategy parameters for different market conditions
- Perform Monte Carlo simulations to assess strategy robustness
- Analyze performance metrics and risk characteristics

For detailed instructions on using the backtesting module, see the [Backtesting Guide](backend/exchange/backtesting/README.md).

## Contributing

Please see our [Contributing Guidelines](docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

## Production Deployment

The ETRMS system can be deployed to a production environment using Docker and Docker Compose. A comprehensive deployment guide and automated deployment script are provided to simplify the process.

### Quick Deployment to riskmanage.xyz

1. Ensure your server has Docker and Docker Compose installed
2. Clone this repository to your server
3. Run the deployment script as root:
   ```bash
   sudo ./scripts/deploy_production.sh
   ```

For detailed deployment instructions, see the [Production Deployment Guide](docs/deployment/PRODUCTION_DEPLOYMENT.md). 