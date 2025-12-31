#!/bin/bash
# Backend startup script

echo "Starting AI Document Analyzer Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Initialize database
echo "Initializing database..."
python database.py

# Start FastAPI server
echo "Starting FastAPI server on http://localhost:8000"
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
