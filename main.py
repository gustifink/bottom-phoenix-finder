#!/usr/bin/env python3

import os
import sys
import subprocess

# Add backend to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Change to backend directory
os.chdir(backend_dir)

# Set PYTHONPATH
os.environ['PYTHONPATH'] = backend_dir

# Get port from environment or default to 8000
port = os.environ.get('PORT', '8000')

# Run the FastAPI server
if __name__ == "__main__":
    subprocess.run([
        sys.executable, '-m', 'uvicorn', 
        'app.main:app', 
        '--host', '0.0.0.0', 
        '--port', port
    ]) 