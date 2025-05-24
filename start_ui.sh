#!/bin/bash

# Invasive Species Tracker UI Startup Script
echo "🚀 Starting Invasive Species Tracker UI..."

# Check if we're in the right directory
if [ ! -f "web_app.py" ]; then
    echo "❌ Error: Please run this script from the invasive-species-tracker directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -q Flask Flask-CORS

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure to set up your API keys!"
    echo "   Required variables:"
    echo "   - GOOGLE_CLOUD_PROJECT"
    echo "   - ANTHROPIC_API_KEY"
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "🔑 Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
fi

# Start the application
echo "🌐 Starting web server..."
echo "📍 Open your browser to: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop"
echo ""

python web_app.py