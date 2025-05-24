#!/bin/bash

# Invasive Species Tracker UI Run Script

echo "Starting Invasive Species Tracker UI..."

# Navigate to project directory
cd /Users/adamanzuoni/invasive-species-tracker

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
echo "Installing dependencies..."
pip install -r requirements.txt

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found!"
fi

# Run the web application
echo "Launching web UI at http://localhost:5000"
python web_app.py