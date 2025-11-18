#!/bin/bash

# Load Testing Runner Script
# Runs various load test scenarios against the API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}System Health Analyzer - Load Testing Suite${NC}"
echo "================================================"
echo ""

# Check if API is running
API_HOST=${API_HOST:-http://localhost:8000}
echo -e "${YELLOW}Checking API availability at ${API_HOST}...${NC}"

if curl -s "${API_HOST}/health" > /dev/null; then
    echo -e "${GREEN}✓ API is available${NC}"
else
    echo -e "${RED}✗ API is not available at ${API_HOST}${NC}"
    echo "Please start the API server first: uvicorn src.api.main:app"
    exit 1
fi

# Install dependencies
echo ""
echo -e "${YELLOW}Installing load testing dependencies...${NC}"
pip install -q locust requests

# Run load test scenarios
echo ""
echo -e "${GREEN}Available Load Test Scenarios:${NC}"
echo "1. Quick Test (10 users, 30 seconds)"
echo "2. Normal Load (50 users, 2 minutes)"
echo "3. High Load (100 users, 5 minutes)"
echo "4. Stress Test (200 users, 3 minutes)"
echo "5. Step Load (gradual increase)"
echo "6. Spike Test (sudden traffic spike)"
echo "7. Wave Load (sinusoidal pattern)"
echo "8. Custom (interactive mode)"
echo ""

read -p "Select scenario (1-8): " scenario

case $scenario in
    1)
        echo -e "${YELLOW}Running Quick Test...${NC}"
        locust -f tests/load_testing/locustfile.py \
            --host=${API_HOST} \
            --users 10 \
            --spawn-rate 2 \
            --run-time 30s \
            --headless \
            --html reports/load_test_quick.html
        ;;
    2)
        echo -e "${YELLOW}Running Normal Load Test...${NC}"
        locust -f tests/load_testing/locustfile.py \
            --host=${API_HOST} \
            --users 50 \
            --spawn-rate 5 \
            --run-time 2m \
            --headless \
            --html reports/load_test_normal.html
        ;;
    3)
        echo -e "${YELLOW}Running High Load Test...${NC}"
        locust -f tests/load_testing/locustfile.py \
            --host=${API_HOST} \
            --users 100 \
            --spawn-rate 10 \
            --run-time 5m \
            --headless \
            --html reports/load_test_high.html
        ;;
    4)
        echo -e "${YELLOW}Running Stress Test...${NC}"
        locust -f tests/load_testing/locustfile.py \
            --host=${API_HOST} \
            --users 200 \
            --spawn-rate 20 \
            --run-time 3m \
            --headless \
            --html reports/load_test_stress.html
        ;;
    5)
        echo -e "${YELLOW}Running Step Load Test...${NC}"
        locust -f tests/load_testing/locustfile.py \
            --host=${API_HOST} \
            --headless \
            --html reports/load_test_step.html \
            StepLoadShape
        ;;
    6)
        echo -e "${YELLOW}Running Spike Test...${NC}"
        locust -f tests/load_testing/locustfile.py \
            --host=${API_HOST} \
            --headless \
            --html reports/load_test_spike.html \
            SpikeLoadShape
        ;;
    7)
        echo -e "${YELLOW}Running Wave Load Test...${NC}"
        locust -f tests/load_testing/locustfile.py \
            --host=${API_HOST} \
            --headless \
            --html reports/load_test_wave.html \
            WaveLoadShape
        ;;
    8)
        echo -e "${YELLOW}Starting Interactive Mode...${NC}"
        echo "Open http://localhost:8089 in your browser"
        locust -f tests/load_testing/locustfile.py \
            --host=${API_HOST}
        ;;
    *)
        echo -e "${RED}Invalid scenario selected${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Load test completed!${NC}"
echo "Report saved to reports/ directory"
