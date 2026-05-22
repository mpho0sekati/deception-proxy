# ImmuniSOC-Nexus

A safety-first proof of concept for a Zero-Trust deception mesh. The system is designed to detect unauthorized access to a honeytoken route, quarantine the source IP, and display incident status clearly in the SOC dashboard.

## Architecture

- `proxy.go` — Go-based deception proxy. It forwards normal traffic to a local dummy backend, blocks quarantined IPs, detects honeytoken access, and raises alerts to the Brain API.
- `api.py` — FastAPI-based Brain API. It stores alerts in a local SQLite database, generates a structured security report, and writes an audit brief to `threat_report.md`.
- `dashboard.py` — Streamlit dashboard for clear operational visibility and recommended response actions.

## What was improved

- **Database Persistence**: Thread-safe alert storage using SQLite instead of a shared Python list
- **JSON File Persistence**: Alerts are now also persisted to `alerts.json` file for backup/diagnostic purposes
- **Enhanced Security**: Added IP validation and input sanitization to prevent injection attacks
- **API Key Authentication**: Added X-API-Key header authentication on write endpoints for enhanced security
- **CORS Middleware**: Added CORS support for cross-origin requests
- **Reset Endpoint**: Added POST `/reset` endpoint for clean demo resets
- **Clean Dashboard Interface**: Simplified, professional dashboard focusing on key metrics and threat visualization
- **Improved Dashboard Experience**: Replaced time.sleep() loop with st_autorefresh for smoother UI experience without flickering
- **Dashboard Reset Button**: Added Reset button to the dashboard sidebar for easy system resets
- **Clean Disconnect State**: Added st.stop() on connection error for clean disconnect state
- **Optimized Data Fetching**: Moved all data fetching outside the loop into a single clean block
- **Enhanced Dashboard Visualization**: Added system status panel, attack pattern charts, IP frequency analysis, and comprehensive metrics
- **3-Tier Information Hierarchy Dashboard**: Implemented Global Health header (flashing status indicators), KPI metrics row, and live threat feed body
- **Live Auto-Refresh Capability**: Added configurable auto-refresh for real-time monitoring
- **Emergency Crisis Copilot**: Added sidebar with report generation, emergency contacts, and immediate action checklist
- **Enhanced Startup Script**: Added health checks, proper startup order (API → Proxy → Dashboard), ASCII banner, and detailed error messages in start.ps1
- **Enhanced Testing Script**: Added auto-reset at start, multi-IP coordinated attack simulation (triggers CRITICAL state), boxed colored step headers for readability, final status summary, and X-API-Key header to direct Brain API calls in test.ps1
- **Better Error Handling**: Improved error handling throughout all components
- **Auto-refresh Capability**: Added auto-refresh feature to the dashboard for continuous monitoring
- **Improved Logging**: Enhanced logging for better debugging and monitoring
- **Robust Connection Handling**: Better timeout handling and connection management
- **Input Validation**: Added IP address validation and other security checks

## Integration with Existing Infrastructure

To integrate ImmuniSOC-Nexus into existing banking or government infrastructure without "breaking" current systems, you should use the "Sidecar" or "Transparent Proxy" pattern:

### Sidecar Pattern
Deploy ImmuniSOC-Nexus alongside existing services as a sidecar container or process. This allows the system to intercept and inspect traffic without modifying the existing application code.

### Transparent Proxy Pattern
Position ImmuniSOC-Nexus in the network path to transparently inspect traffic between clients and servers. The system operates without requiring any configuration changes on client or server applications.

### Implementation Steps
1. **Traffic Interception**: Configure your network to route specific traffic through ImmuniSOC-Nexus
2. **Honeypot Paths**: Define honeypot endpoints that mimic legitimate system paths but are designed to detect unauthorized access
3. **Alert Integration**: Connect the Brain API to your existing SIEM or monitoring systems
4. **Gradual Rollout**: Start with non-critical systems to validate the integration before expanding to more sensitive areas

### Benefits
- Zero disruption to existing systems
- Enhanced security through deception techniques
- Real-time threat detection and response
- Seamless integration with existing monitoring tools

## Requirements

### Prerequisites

- Python 3.8 or higher
- Go programming language
- Git (for cloning the repository)

### Environment Setup

We recommend using a virtual environment to manage dependencies:

1. **Automatic Setup**: Run the environment setup script:
   ```powershell
   python setup_env.py
   ```

2. **Manual Setup**: If you prefer to set up manually:
   ```powershell
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

### Dependencies

The project requires the following Python packages:
- fastapi
- pydantic
- uvicorn
- streamlit
- requests
- streamlit-autorefresh

**Note**: The Go proxy (`proxy.go`) requires Go to be installed and available in your PATH. A bug with an unused import has been fixed in the latest version.

## Setting up on a new machine

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd immuniSOC-nexus
   ```

2. **Install Go** (if not already installed):
   - Download from https://golang.org/dl/
   - Follow installation instructions for your OS

3. **Install Python dependencies:**
   ```bash
   python setup_env.py
   ```
   OR
   ```powershell
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run the system:**
   ```powershell
   python safe_run.py
   ```
   OR
   ```powershell
   .\start.ps1
   ```

## Single launch command

### Quick Start
Run the safe runner script which will check/create the environment and start all services:
```powershell
python safe_run.py
```

### Using the provided scripts
Run all services from the repository root:

```powershell
.\start.ps1
```

This starts:

- Brain API on `http://localhost:8000`
- ImmuniSOC-Nexus proxy on `http://localhost:8080`
- Streamlit dashboard on `http://localhost:8501`

Alternative launch scripts:
- `run_services.bat` - Windows batch script
- `run_services.ps1` - Windows PowerShell script

The `start.ps1` script now includes:
- Health checks to verify each service is running before starting the next
- Proper startup order: API → Proxy → Dashboard
- ASCII banner for better visual presentation
- Detailed error messages that tell you exactly what to fix if services fail to start

## API Endpoints

The Brain API exposes the following endpoints:

- `POST /alert` - Create a new alert (requires X-API-Key header)
- `GET /status` - Get current alert status
- `GET /report` - Generate security report
- `POST /reset` - Reset all alerts (requires X-API-Key header)

## Dashboard Features

The SOC dashboard (`dashboard.py`) provides:

### Key Security Metrics
- Total Attacks Blocked
- Active Quarantined IPs
- Current Threat Level

### Live Threat Feed
- Real-time event streaming from the proxy
- Historical threat data with timestamps
- Auto-refresh capability

### Threat Analysis
- Current threat summary
- Layman explanation of the threat
- Actionable recommendations

## How to use

1. Open the dashboard at `http://localhost:8501`
2. Send normal traffic through the proxy, for example:
   - `http://localhost:8080/api/v1/public-news`
3. Simulate an attack by requesting the honeypot path:
   - `http://localhost:8080/api/v2/financial-export`
4. The proxy will quarantine the attacking IP and the dashboard will update the incident status.

## Testing

Run the defensive validation script:

```powershell
.\test.ps1
```

The script now includes:
- Auto-reset at the start of every run (clean slate)
- Step 1: Normal traffic test (should succeed)
- Step 2: Honeypot trigger test (should quarantine the IP)
- Step 3: Quarantine verification (subsequent requests from same IP should fail)
- Step 4: Multi-IP coordinated attack that triggers CRITICAL state
- Boxed colored step headers for readability on screen recordings
- Final status summary showing total quarantined IPs
- X-API-Key header to direct Brain API calls

## Customization

Environment variables that may be set before launch:

- `PROXY_PORT` — default `8080`
- `BACKEND_ADDR` — default `127.0.0.1:8081`
- `BRAIN_API_URL` — default `http://localhost:8000/alert`
- `HONEYTOKEN_PATH` — default `/api/v2/financial-export`
- `API_KEY` — API key for write endpoints (auto-generated if not set)

## Audit output

The Brain API writes `threat_report.md` every time the report endpoint is requested, keeping the latest security brief available for review