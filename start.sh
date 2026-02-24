#!/bin/bash

# Business Signal Analyzer - Start Script
echo "🚀 Starting Business Signal Analyzer..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Initialize database if needed
echo "📦 Initializing database..."
cd backend
python -c "from storage.database import init_db; init_db()" 2>/dev/null || echo "Database already initialized"

# Start the backend
echo "🔥 Starting FastAPI server on http://localhost:8000"
echo "📖 API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py
