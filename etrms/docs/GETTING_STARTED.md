# Getting Started with ETRMS Development

This guide helps new developers get started with contributing to the Enhanced Trading Risk Management System (ETRMS). It covers setting up your development environment, understanding the project structure, and guidance on implementing missing components.

## Current Project Status

The ETRMS project is currently under active development. The frontend UI components and documentation are largely complete, but many backend components still need to be implemented. Please refer to [DEVELOPMENT.md](DEVELOPMENT.md) for a detailed breakdown of what's implemented and what's missing.

## Development Environment Setup

### Prerequisites

- Python 3.9+
- Node.js 16+ and npm
- PostgreSQL 14+
- Redis 7+ (optional for initial development)
- Git
- Docker and Docker Compose (optional but recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-organization/etrms.git
cd etrms
```

### Step 2: Set Up the Backend

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt
```

### Step 3: Set Up the Frontend

```bash
# Navigate to the frontend directory
cd ../frontend

# Install frontend dependencies
npm install
```

### Step 4: Set Up the Database

```bash
# Install PostgreSQL if not already installed
# On Ubuntu:
# sudo apt update
# sudo apt install postgresql postgresql-contrib

# Create a database
# sudo -u postgres createdb etrms
```

### Step 5: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your database credentials and other settings
# nano .env
```

Example `.env` file content:

```
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=etrms
DB_USER=postgres
DB_PASSWORD=your_password

# API Configuration
API_SECRET_KEY=development_secret_key
JWT_SECRET=development_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000"]

# Exchange API Keys (Not required for initial development)
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=true

# AI Assistant Configuration (Not required for initial development)
AI_ASSISTANT_API_KEY=
```

### Step 6: Run the Development Servers

#### Backend

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm run dev
```

Access the frontend at http://localhost:3000 and the API documentation at http://localhost:8000/docs

## Project Structure Overview

Understanding the project structure is crucial for effective contribution:

```
etrms/
├── backend/                         # Python FastAPI backend
│   ├── api/                         # API endpoints
│   ├── core/                        # Core business logic
│   │   ├── risk_engine/             # Risk management logic
│   │   ├── market_analyzer/         # Market analysis logic
│   │   └── ai_assistant/            # AI assistant logic
│   ├── data/                        # Data handling and persistence
│   │   ├── models/                  # Database models
│   │   ├── repositories/            # Data access layer
│   │   └── services/                # Data processing services
│   ├── exchange/                    # Exchange integration
│   │   ├── binance/                 # Binance API client
│   │   ├── hyperliquid/             # Hyperliquid API client
│   │   └── common/                  # Common exchange functionality
│   ├── config/                      # Configuration
│   ├── utils/                       # Utility functions
│   └── tests/                       # Tests
├── frontend/                        # React frontend
├── docs/                            # Documentation
└── database/                        # Database migrations and seeds
```

## Implementation Guidance

### First Steps for New Developers

1. **Understand the Architecture**: Read the [DEVELOPMENT.md](DEVELOPMENT.md) and [architectural documentation](architecture/OVERVIEW.md) to understand the system design.

2. **Check the Implementation Plan**: Review [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) to understand the prioritized tasks.

3. **Start with Simple Components**: Begin by implementing straightforward components like database models or completing API endpoint logic.

### Recommended First Tasks

For new contributors, the following tasks are good starting points:

1. **Database Models**:
   - Implement the Account model in `backend/data/models/accounts.py`
   - Implement the Trade model in `backend/data/models/trades.py`
   - Implement the RiskConfiguration model in `backend/data/models/risk_configurations.py`

2. **Exchange Integration**:
   - Complete the Binance Futures client implementation in `backend/exchange/binance/binance_futures_client.py`
   - Implement basic functionality like fetching account information and positions

3. **Basic API Implementation**:
   - Complete the account endpoints implementation in `backend/api/accounts.py`
   - Complete the position endpoints implementation in `backend/api/positions.py`

## Development Workflow

1. **Create a Branch**: Always create a new branch for your work
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement Changes**: Follow the existing code style and architecture

3. **Add Tests**: Write tests for your implementations
   ```bash
   cd backend
   pytest tests/your_test_file.py
   ```

4. **Run Linting**: Ensure code quality
   ```bash
   flake8 backend
   ```

5. **Submit a Pull Request**: When your feature is complete and tested

## Running with Docker (Optional)

If you prefer using Docker for development:

```bash
# Build and start the services
docker-compose -f docker/docker-compose.dev.yml up --build

# Stop the services
docker-compose -f docker/docker-compose.dev.yml down
```

## Debugging Tips

1. **API Debugging**: Use the FastAPI documentation at http://localhost:8000/docs for testing API endpoints

2. **Frontend Debugging**: Use React Developer Tools and browser console for debugging frontend issues

3. **Database Debugging**: Use a tool like pgAdmin or DBeaver to inspect the database

4. **Backend Logging**: Check the console output from the backend server for log messages

## Getting Help

If you need assistance:

1. Check the documentation in the `docs` directory
2. Review the code comments
3. Reach out to the project maintainers

## Next Steps

After setting up your environment and completing your first tasks, consider the following:

1. Implement higher-priority components from the [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
2. Help improve test coverage
3. Contribute to documentation updates

Welcome to the ETRMS project, and happy coding! 