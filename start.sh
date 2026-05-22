#!/bin/bash

# ImmuniSOC-Nexus startup script for Linux/macOS

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
  _____              _   _       _   _      _   
 |_   _|__  _ __ ___| |_| | __ _| |_(_) ___| | __
   | |/ _ \| '__/ __| __| |/ _` | __| |/ __| |/ /
   | | (_) | |  \__ \ |_| | (_| | |_| | (__|   < 
   |_|\___/|_|  |___/\__|_|\__,_|\__|_|\___|_|\_\

  ImmuniSOC-Nexus
  Starting Services in Order: API → Proxy → Dashboard
EOF
echo -e "${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}Error: python3 is not installed${NC}" >&2
    exit 1
fi

if ! command_exists go; then
    echo -e "${RED}Error: go is not installed${NC}" >&2
    exit 1
fi

if ! command_exists pip; then
    echo -e "${RED}Error: pip is not installed${NC}" >&2
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites found${NC}"

# Generate API key if not set
if [ -z "$API_KEY" ]; then
    export API_KEY=$(openssl rand -hex 16)
    echo -e "${YELLOW}Generated API Key: ${API_KEY:0:8}...${NC}"
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Error: Virtual environment not found. Run setup_env.py first.${NC}" >&2
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Function to check if a service is running on a given port
check_port() {
    local port=$1
    if command_exists lsof; then
        lsof -Pi :$port -sTCP:LISTEN -t >/dev/null
    elif command_exists netstat; then
        netstat -an 2>/dev/null | grep LISTEN | grep ":$port " >/dev/null
    else
        # Fallback: try to connect
        (echo > /dev/tcp/localhost/$port) >/dev/null 2>&1
    fi
}

# Function to wait for a service to be healthy
wait_for_service() {
    local port=$1
    local service_name=$2
    local timeout=${3:-30}
    
    echo -e "${BLUE}Waiting for $service_name to be available on port $port...${NC}"
    
    local count=0
    while [ $count -lt $timeout ]; do
        if check_port $port; then
            echo -e "${GREEN}✓ $service_name is healthy on port $port${NC}"
            return 0
        fi
        sleep 1
        ((count++))
    done
    
    echo -e "${RED}✗ Timeout waiting for $service_name on port $port. Service may have failed to start.${NC}"
    echo -e "${RED}Possible fixes:${NC}"
    echo -e "${RED}  - Check if another process is using port $port${NC}"
    echo -e "${RED}  - Verify Go is installed for the proxy service${NC}"
    return 1
}

echo -e "${BLUE}Starting services in order: API → Proxy → Dashboard...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo

# 1. Start the Brain API in background
echo -e "${GREEN}Step 1: Starting Brain API on Port 8000...${NC}"
export API_KEY="$API_KEY"
python3 api.py &
API_PID=$!
sleep 2

# Wait for API to be healthy before continuing
if ! wait_for_service 8000 "Brain API"; then
    echo -e "${RED}Cannot proceed: Brain API failed to start.${NC}"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✓ Brain API started successfully!${NC}"

# 2. Start the ImmuniSOC-Nexus Go proxy in background
echo -e "${GREEN}Step 2: Starting ImmuniSOC-Nexus Go Proxy on Port 8080...${NC}"
export BRAIN_API_URL="http://localhost:8000/alert"
export API_KEY="$API_KEY"
go run proxy.go &
PROXY_PID=$!
sleep 2

# Wait for Proxy to be healthy before continuing
if ! wait_for_service 8080 "ImmuniSOC-Nexus Go Proxy"; then
    echo -e "${RED}Cannot proceed: ImmuniSOC-Nexus Go Proxy failed to start.${NC}"
    echo -e "${RED}Possible fixes:${NC}"
    echo -e "${RED}  - Ensure Go is installed and available in your PATH${NC}"
    echo -e "${RED}  - Run 'go version' to verify Go installation${NC}"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✓ ImmuniSOC-Nexus Go Proxy started successfully!${NC}"

# 3. Start the Streamlit dashboard
echo -e "${GREEN}Step 3: Starting Streamlit dashboard on Port 8501...${NC}"
export API_URL="http://localhost:8000"
export API_KEY="$API_KEY"
streamlit run dashboard.py --server.headless true --browser.gatherUsageStats false

echo -e "${BLUE}Services started. Press Ctrl+C to stop.${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    kill $API_PID $PROXY_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM
wait $API_PID $PROXY_PID