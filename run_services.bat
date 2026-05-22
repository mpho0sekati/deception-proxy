@echo off
echo  _____              _   _       _   _      _   
echo |_   _|__  _ __ ___| |_| | __ _| |_(_) ___| | __
echo   | |/ _ \| '__/ __| __| |/ _` | __| |/ __| |/ /
echo   | | (_) | |  \__ \ |_| | (_| | |_| | (__|   < 
echo   |_|\___/|_|  |___/\__|_|\__,_|\__|_|\___|_|\_\
echo.
echo   ImmuniSOC-Nexus
echo   Running Services in Order: API ^-> Proxy ^-> Dashboard
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo Error: Could not activate virtual environment. Make sure it exists.
    pause
    exit /b 1
)

echo Virtual environment activated!

REM Generate a random API key if not set
if "%API_KEY%"=="" (
    for /f %%i in ('powershell -command "[System.Web.Security.Membership]::GeneratePassword(32, 4) -replace '[^a-zA-Z0-9]', 'A'"') do set "API_KEY=%%i"
    echo Generated API Key for this session: %API_KEY:~0,8%...
)

echo Starting services in order: API ^-> Proxy ^-> Dashboard...
echo Press Ctrl+C to stop all services
echo.

REM Start the Brain API in background
echo Step 1: Starting Brain API on Port 8000...
set API_KEY=%API_KEY%
start "Brain API" cmd /c "set API_KEY=%API_KEY%^& echo Starting Brain API... ^& python api.py ^& echo Brain API stopped. Press any key to exit. ^& pause"

REM Brief wait for API to potentially start
timeout /t 5 /nobreak >nul

REM Check if API is running (basic check)
echo Checking if Brain API is available...
curl -s --connect-timeout 5 http://localhost:8000/status >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Brain API may not be running properly
    echo Possible fixes:
    echo   - Check if another process is using port 8000
    echo   - Check the Brain API console window for errors
    echo.
) else (
    echo [CHECK] Brain API appears to be running
)

REM Start the ImmuniSOC-Nexus Go proxy in background
echo Step 2: Starting ImmuniSOC-Nexus Go Proxy on Port 8080...
set BRAIN_API_URL=http://localhost:8000/alert
set API_KEY=%API_KEY%
start "ImmuniSOC-Nexus Proxy" cmd /c "set BRAIN_API_URL=http://localhost:8000/alert^& set API_KEY=%API_KEY%^& echo Starting Go Proxy... ^& go run proxy.go ^& echo Go Proxy stopped. Press any key to exit. ^& pause"

REM Brief wait for Proxy to potentially start
timeout /t 5 /nobreak >nul

REM Check if Proxy is running (basic check)
echo Checking if ImmuniSOC-Nexus Proxy is available...
curl -s --connect-timeout 5 http://localhost:8080/status >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: ImmuniSOC-Nexus Proxy may not be running properly
    echo Possible fixes:
    echo   - Ensure Go is installed and available in your PATH
    echo   - Run 'go version' to verify Go installation
    echo   - Check the Go Proxy console window for errors
    echo.
) else (
    echo [CHECK] ImmuniSOC-Nexus Proxy appears to be running
)

REM Start the Streamlit dashboard (this will open in the foreground)
echo Step 3: Starting Streamlit dashboard on Port 8501...
set API_URL=http://localhost:8000
set API_KEY=%API_KEY%
echo Starting Streamlit dashboard... The UI should open in your browser shortly.
streamlit run dashboard.py

pause