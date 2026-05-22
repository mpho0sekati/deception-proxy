#!/usr/bin/env python3
"""
Safe Run Script for ImmuniSOC-Nexus
This script checks if the environment is set up correctly and runs the project.
"""
import subprocess
import sys
import os
import platform
import time
import threading
import secrets
import socket
from pathlib import Path

def check_virtual_environment():
    """Check if the virtual environment exists."""
    venv_path = Path("venv")
    python_executable = "python.exe" if platform.system() == "Windows" else "python"
    python_path = venv_path / ("Scripts" if platform.system() == "Windows" else "bin") / python_executable
    
    return venv_path.exists() and python_path.exists()

def check_requirements_installed():
    """Check if required packages are installed in the virtual environment."""
    if not check_virtual_environment():
        return False
    
    # Determine the path to python in the virtual environment
    python_executable = "python.exe" if platform.system() == "Windows" else "python"
    python_path = Path("venv") / ("Scripts" if platform.system() == "Windows" else "bin") / python_executable
    
    # Try importing the required packages
    try:
        # Run a Python command in the virtual environment to check for packages
        result = subprocess.run([
            str(python_path), "-c", 
            "import fastapi, uvicorn, streamlit, requests"
        ], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def setup_environment():
    """Set up the virtual environment and install requirements."""
    print("Setting up the environment...")
    
    # Create requirements.txt if it doesn't exist
    requirements_txt = Path("requirements.txt")
    if not requirements_txt.exists():
        print("Creating requirements.txt...")
        with open(requirements_txt, "w") as f:
            f.write("""fastapi==0.104.1
pydantic==2.5.0
uvicorn==0.24.0
streamlit==1.29.0
requests==2.31.0
streamlit-autorefresh==1.0.1""")
        print("✓ requirements.txt created!")
    
    # Create virtual environment
    print("Creating virtual environment...")
    result = subprocess.run([sys.executable, "-m", "venv", "venv"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"✗ Error creating virtual environment: {result.stderr}")
        return False
    
    print("✓ Virtual environment created!")
    
    # Determine the path to pip in the virtual environment
    pip_executable = "pip.exe" if platform.system() == "Windows" else "pip"
    pip_path = Path("venv") / ("Scripts" if platform.system() == "Windows" else "bin") / pip_executable
    
    # Upgrade pip
    print("Upgrading pip...")
    result = subprocess.run([str(pip_path), "install", "--upgrade", "pip"], 
                           capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Could not upgrade pip: {result.stderr}")
    
    # Install requirements
    print("Installing requirements...")
    result = subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], 
                           capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Requirements installed successfully!")
        return True
    else:
        print(f"✗ Error installing requirements: {result.stderr}")
        return False

def is_port_available(host, port, timeout=5):
    """Check if a port is available."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0  # Port is available if connection fails
    except:
        return True

def wait_for_service(host, port, service_name, timeout=30):
    """Wait for a service to become available."""
    print(f"Waiting for {service_name} on {host}:{port}...")
    
    timeout_time = time.time() + timeout
    while time.time() < timeout_time:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:  # Port is open
                print(f"✓ {service_name} is available on {host}:{port}")
                return True
        except:
            pass
        
        time.sleep(1)
    
    print(f"✗ Timeout waiting for {service_name} on {host}:{port}")
    print("Possible fixes:")
    print(f"  - Check if another process is using port {port}")
    print(f"  - Verify the {service_name} started without errors")
    return False

def run_command_with_env(cmd, name, env_vars=None):
    """Run a command in a subprocess with custom environment variables."""
    try:
        print(f"Starting {name}...")
        
        # Update environment with provided variables
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        result = subprocess.run(cmd, shell=True, env=env)
        print(f"{name} exited with code: {result.returncode}")
    except KeyboardInterrupt:
        print(f"{name} interrupted by user")

def run_api(api_key):
    """Run the API server."""
    env = os.environ.copy()
    env['API_KEY'] = api_key
    
    if platform.system() == "Windows":
        cmd = r"venv\Scripts\python.exe api.py"
    else:
        cmd = "venv/bin/python api.py"
    run_command_with_env(cmd, "API Server", env)

def run_proxy(api_key):
    """Run the proxy server."""
    env = os.environ.copy()
    env['BRAIN_API_URL'] = 'http://localhost:8000/alert'
    env['API_KEY'] = api_key
    
    cmd = "go run proxy.go"
    run_command_with_env(cmd, "ImmuniSOC-Nexus Proxy Server", env)

def run_dashboard(api_key):
    """Run the dashboard."""
    env = os.environ.copy()
    env['API_URL'] = 'http://localhost:8000'
    env['API_KEY'] = api_key
    
    if platform.system() == "Windows":
        cmd = r"venv\Scripts\streamlit.exe run dashboard.py"
    else:
        cmd = "venv/bin/streamlit run dashboard.py"
    run_command_with_env(cmd, "Dashboard", env)

def main():
    print("🛡️  ImmuniSOC-Nexus")
    print("   Safe Runner with Health Checks")
    print("="*50)
    
    # Check if environment exists
    if not check_virtual_environment():
        print("Virtual environment not found.")
        response = input("Would you like to create it now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            if not setup_environment():
                print("Failed to set up the environment. Exiting.")
                sys.exit(1)
        else:
            print("Environment setup cancelled. Exiting.")
            sys.exit(1)
    else:
        print("✓ Virtual environment found!")
        
        # Check if packages are installed
        if not check_requirements_installed():
            print("Required packages not found in the virtual environment.")
            response = input("Would you like to install them now? (y/n): ")
            if response.lower() in ['y', 'yes']:
                if not setup_environment():
                    print("Failed to install requirements. Exiting.")
                    sys.exit(1)
            else:
                print("Requirements installation cancelled. Exiting.")
                sys.exit(1)
        else:
            print("✓ All required packages are installed!")
    
    # Generate API key
    api_key = os.environ.get('API_KEY') or secrets.token_urlsafe(32)
    print(f"Using API Key: {api_key[:8]}...")
    
    print("\nStarting ImmuniSOC-Nexus services in order: API → Proxy → Dashboard...")
    print("The Brain API will start on http://localhost:8000")
    print("The ImmuniSOC-Nexus Proxy will start on http://localhost:8080")
    print("The Dashboard will start on http://localhost:8501")
    print("\nPress Ctrl+C to stop all services\n")
    
    # Start services in the correct order with health checks
    print("Step 1: Starting Brain API on Port 8000...")
    api_thread = threading.Thread(target=run_api, args=(api_key,))
    api_thread.start()
    
    # Wait for API to be available before starting the proxy
    if not wait_for_service("localhost", 8000, "Brain API", timeout=45):
        print("Cannot proceed: Brain API failed to start.")
        sys.exit(1)
    
    print("\nStep 2: Starting ImmuniSOC-Nexus Proxy on Port 8080...")
    proxy_thread = threading.Thread(target=run_proxy, args=(api_key,))
    proxy_thread.start()
    
    # Wait for Proxy to be available before starting the dashboard
    if not wait_for_service("localhost", 8080, "ImmuniSOC-Nexus Proxy", timeout=45):
        print("Cannot proceed: ImmuniSOC-Nexus Proxy failed to start.")
        print("Possible fixes:")
        print("  - Ensure Go is installed and available in your PATH")
        print("  - Run 'go version' to verify Go installation")
        sys.exit(1)
    
    print("\nStep 3: Starting Dashboard on Port 8501...")
    dashboard_thread = threading.Thread(target=run_dashboard, args=(api_key,))
    dashboard_thread.start()
    
    try:
        # Wait for all threads to complete
        api_thread.join()
        proxy_thread.join()
        dashboard_thread.join()
    except KeyboardInterrupt:
        print("\n\nStopping services...")

if __name__ == "__main__":
    main()