@echo off
echo.
echo ================================================
echo    IMMUNISOC-NEXUS - EASY START
echo ================================================
echo.
echo This script will:
echo 1. Setup the environment if needed
echo 2. Start all ImmuniSOC-Nexus services
echo 3. Monitor the system
echo.
echo Press any key to continue or Ctrl+C to cancel
pause >nul

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if Go is available
go version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Go is not installed or not in PATH
    echo Please install Go and try again
    pause
    exit /b 1
)

REM Setup environment if needed
if not exist "venv" (
    echo.
    echo Setting up environment...
    python setup_env.py
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to setup environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo ERROR: Could not activate virtual environment
    pause
    exit /b 1
)

echo.
echo ================================================
echo Starting ImmuniSOC-Nexus services...
echo ================================================
echo.
echo Services will be available at:
echo - Brain API:      http://localhost:8000
echo - Proxy:          http://localhost:8080
echo - Dashboard:      http://localhost:8501
echo.
echo Close this window to stop all services
echo ================================================
echo.

REM Start the safe runner which manages all services
python safe_run.py

echo.
echo ================================================
echo ImmuniSOC-Nexus stopped
echo ================================================
echo.
echo To start again, run this script: EASY_START.bat
echo For more information, check INSTALL.md
echo.
pause