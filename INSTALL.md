# ImmuniSOC-Nexus Installation Guide

This guide will help you set up and run ImmuniSOC-Nexus on a new machine.

## Prerequisites

Before you begin, ensure your system has the following installed:

- **Python 3.8 or higher**
- **Go programming language**
- **Git**

### Installing Prerequisites

#### On Windows:
1. **Python**: Download from [python.org](https://www.python.org/downloads/)
2. **Go**: Download from [golang.org](https://golang.org/dl/)
3. **Git**: Download from [git-scm.com](https://git-scm.com/)

#### On macOS:
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install prerequisites
brew install python3 go git
```

#### On Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip golang git
```

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/mpho0sekati/immunisoc-nexus.git
cd immunisoc-nexus
```

### 2. Install Dependencies
The project includes an automatic setup script that will create a virtual environment and install all required dependencies:

```bash
python setup_env.py
```

This script will:
- Create a Python virtual environment
- Install all required Python packages
- Verify that Go is installed

### 3. Run the System
You have several options to run the system:

#### Option A: Using the Safe Runner (Recommended)
```bash
python safe_run.py
```
This script will:
- Check if the environment is properly set up
- Start all services in the correct order (API → Proxy → Dashboard)
- Perform health checks to ensure each service is running
- Show helpful error messages if anything goes wrong

#### Option B: Using the PowerShell Script
```bash
.\start.ps1
```
This script will:
- Start all services in the correct order
- Show health checks and status
- Provide helpful error messages
- Show an ASCII banner

#### Option C: Manual Start
```bash
# Terminal 1: Start the API
python api.py

# Terminal 2: Start the Proxy (after API is running)
go run proxy.go

# Terminal 3: Start the Dashboard (after API and Proxy are running)
streamlit run dashboard.py
```

## Verification

Once all services are running, you can verify the system is working:

1. **API**: Open `http://localhost:8000/status` in your browser
2. **Proxy**: Make a test request: `curl http://localhost:8080/api/v1/public-news`
3. **Dashboard**: Open `http://localhost:8501` in your browser

## Testing the System

Run the test script to verify all functionality:
```bash
.\test.ps1
```

This will:
- Auto-reset the system
- Test normal traffic
- Trigger the honeypot
- Verify quarantine functionality
- Simulate multi-IP attacks
- Show final status summary

## Ports Used

- **8000**: Brain API
- **8080**: ImmuniSOC-Nexus Proxy
- **8081**: Dummy Backend
- **8501**: Streamlit Dashboard

## Troubleshooting

### Common Issues:

1. **Port already in use**: Make sure no other applications are using the required ports
2. **Python modules not found**: Ensure you activated the virtual environment
3. **Go not found**: Verify Go is installed and in your PATH
4. **Permission errors**: Run the scripts with appropriate permissions

### Reset the System
If you need to reset the system to a clean state:
```bash
# Use the API endpoint with proper API key
curl -X POST http://localhost:8000/reset -H "X-API-Key: YOUR_API_KEY_HERE"
```

## Stopping the System

To stop all services, press `Ctrl+C` in each terminal window where services are running.

## Docker Alternative (Optional)

If you prefer to use Docker, you can build and run the system using Docker Compose:

```bash
docker-compose up --build
```

This will start all services in containers with proper networking.

---

That's it! Your ImmuniSOC-Nexus system should now be running and ready to demonstrate advanced deception mesh capabilities.