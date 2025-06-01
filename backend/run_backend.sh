#!/bin/bash

# Navigate to backend directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Start the backend
echo "Starting Bottom backend..."
python3 app/main.py 