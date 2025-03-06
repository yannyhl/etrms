#!/bin/bash
# Run tests for the Enhanced Trading Risk Management System (ETRMS)

# Set colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ALL=false
UNIT=false
INTEGRATION=false
E2E=false
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""

# Display usage information
usage() {
    echo -e "${BLUE}Enhanced Trading Risk Management System (ETRMS) Testing Script${NC}"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -a, --all         Run all tests"
    echo "  -u, --unit        Run unit tests only"
    echo "  -i, --integration Run integration tests only"
    echo "  -e, --e2e         Run end-to-end tests only"
    echo "  -c, --coverage    Generate coverage report"
    echo "  -v, --verbose     Display verbose output"
    echo "  -t, --test TEST   Run a specific test file, module, or function"
    echo "  -h, --help        Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --all                           Run all tests"
    echo "  $0 --unit --coverage               Run unit tests with coverage report"
    echo "  $0 --test tests/unit/api/test_positions.py  Run tests in a specific file"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            ALL=true
            shift
            ;;
        -u|--unit)
            UNIT=true
            shift
            ;;
        -i|--integration)
            INTEGRATION=true
            shift
            ;;
        -e|--e2e)
            E2E=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}" >&2
            usage
            exit 1
            ;;
    esac
done

# Check if Python virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}No active virtual environment detected.${NC}"
    echo -e "It's recommended to run tests within a virtual environment."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install test dependencies if needed
echo -e "${BLUE}Checking test dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov

# Build test command
CMD="python -m pytest"

if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    CMD="$CMD --cov=. --cov-report=term-missing"
fi

if [ "$SPECIFIC_TEST" != "" ]; then
    CMD="$CMD $SPECIFIC_TEST"
elif [ "$ALL" = true ]; then
    CMD="$CMD tests/"
elif [ "$UNIT" = true ] && [ "$INTEGRATION" = true ] && [ "$E2E" = true ]; then
    CMD="$CMD tests/"
elif [ "$UNIT" = true ] && [ "$INTEGRATION" = true ]; then
    CMD="$CMD tests/unit/ tests/integration/"
elif [ "$UNIT" = true ] && [ "$E2E" = true ]; then
    CMD="$CMD tests/unit/ tests/e2e/"
elif [ "$INTEGRATION" = true ] && [ "$E2E" = true ]; then
    CMD="$CMD tests/integration/ tests/e2e/"
elif [ "$UNIT" = true ]; then
    CMD="$CMD tests/unit/"
elif [ "$INTEGRATION" = true ]; then
    CMD="$CMD tests/integration/"
elif [ "$E2E" = true ]; then
    CMD="$CMD tests/e2e/"
else
    # If no test type specified, run all tests
    CMD="$CMD tests/"
fi

# Run the tests
echo -e "${BLUE}Running tests with command:${NC} $CMD"
echo ""
eval $CMD

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All tests passed successfully!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi 