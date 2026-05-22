import subprocess
import sys
import os
import platform

def check_virtual_environment():
    """Check if the virtual environment exists."""
    venv_path = os.path.join(os.getcwd(), "venv")
    python_path = os.path.join(venv_path, "Scripts" if platform.system() == "Windows" else "bin", "python.exe" if platform.system() == "Windows" else "python")
    return os.path.exists(venv_path) and os.path.isfile(python_path)

def create_virtual_environment():
    """Create a virtual environment for the ImmuniSOC-Nexus project."""
    print("Setting up virtual environment for ImmuniSOC-Nexus...")
    
    # Check if venv already exists
    if check_virtual_environment():
        print("✓ Virtual environment already exists!")
        return True
    
    # Create venv
    print("Creating virtual environment...")
    result = subprocess.run([sys.executable, "-m", "venv", "venv"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Virtual environment created successfully!")
    else:
        print(f"✗ Error creating virtual environment: {result.stderr}")
        return False
    
    # Determine the path to pip in the virtual environment
    if platform.system() == 'Windows':
        pip_path = os.path.join("venv", "Scripts", "pip.exe")
        python_path = os.path.join("venv", "Scripts", "python.exe")
    else:  # Unix/Linux/macOS
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")
    
    # Upgrade pip
    print("Upgrading pip...")
    result = subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], 
                           capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Could not upgrade pip: {result.stderr}")
    
    # Install requirements
    print("Installing requirements...")
    if os.path.exists("requirements.txt"):
        result = subprocess.run([pip_path, "install", "-r", "requirements.txt"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Requirements installed successfully!")
        else:
            print(f"✗ Error installing requirements: {result.stderr}")
            return False
    else:
        print("✗ requirements.txt not found!")
        return False
    
    return True

def run_project():
    """Run the ImmuniSOC-Nexus project."""
    if not check_virtual_environment():
        print("Virtual environment does not exist. Creating one...")
        if not create_virtual_environment():
            print("Failed to create virtual environment. Exiting.")
            return False
    
    print("\nThe virtual environment is ready!")
    print("\nTo run the project manually, activate the environment and run each service:")
    if platform.system() == 'Windows':
        print("  venv\\Scripts\\activate")
    else:
        print("  source venv/bin/activate")
    print("  python api.py          # Start the Brain API")
    print("  go run proxy.go        # Start the Go proxy")
    print("  streamlit run dashboard.py  # Start the dashboard")
    print("\nOr use the run_services script to start all services at once.")
    
    return True

def main():
    """Main function to handle environment setup."""
    print("ImmuniSOC-Nexus Environment Setup")
    print("="*40)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("Creating requirements.txt file...")
        with open("requirements.txt", "w") as f:
            f.write("""fastapi==0.104.1
pydantic==2.5.0
uvicorn==0.24.0
streamlit==1.29.0
requests==2.31.0
streamlit-autorefresh==1.0.1""")
        print("✓ requirements.txt created!")
    
    # Run the project setup
    success = run_project()
    
    if success:
        print("\n✓ Environment setup completed successfully!")
    else:
        print("\n✗ Environment setup failed!")

if __name__ == "__main__":
    main()