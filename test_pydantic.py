# This will show you the Python interpreter in the virtual environment

"""
Diagnostic script to test pydantic import
"""

try:
    import pydantic
    print(f"✓ pydantic imported successfully! Version: {pydantic.__version__}")
    
    # Test importing specific components used in api.py
    from pydantic import BaseModel, Field
    print("✓ Successfully imported BaseModel and Field from pydantic")
    
    # Test creating a simple model
    class TestModel(BaseModel):
        name: str = Field(..., description="Test field")
    
    test_instance = TestModel(name="test")
    print(f"✓ Successfully created pydantic model instance: {test_instance}")
    
except ImportError as e:
    print(f"✗ Failed to import pydantic: {e}")
    
    # Try to list installed packages to see if pydantic is there
    import subprocess
    import sys
    result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
    print("\nInstalled packages:")
    print(result.stdout)
    
except Exception as e:
    print(f"✗ Unexpected error with pydantic: {e}")