#!/bin/bash

# Enhanced Trading Risk Management System Development Script

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup first..."
    ./scripts/setup.sh
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker to run the development environment."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose to run the development environment."
    exit 1
fi

# Start the development environment
echo "Starting development environment..."
docker-compose -f docker/docker-compose.dev.yml up -d

echo "Development environment started!"
echo "Backend API is running at: http://localhost:8000"
echo "Frontend is running at: http://localhost:3000"
echo "API Documentation is available at: http://localhost:8000/docs"
echo ""
echo "To stop the development environment, run: docker-compose -f docker/docker-compose.dev.yml down" 