#!/bin/bash

echo "Starting Tipping Point - Invasive Species Tracker Web UI"
echo "========================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install web dependencies
echo "Installing dependencies..."
pip install -r requirements_web.txt

# Create necessary directories
mkdir -p templates static

# Start the Flask application
echo ""
echo "Starting web server..."
echo "Access the UI at: http://localhost:5000"
echo ""
python web_app.py