#!/bin/bash

# Start Bottom - Phoenix Token Finder

echo "🔥 Starting Bottom - Phoenix Token Finder..."
echo ""

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ]; then
    echo "📦 Setting up backend virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Backend virtual environment found"
fi

# Start backend
echo ""
echo "🚀 Starting backend server..."
cd backend
source venv/bin/activate
export PYTHONPATH=$(pwd):$PYTHONPATH
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running!"
else
    echo "❌ Backend failed to start. Check the logs."
fi

# Start frontend
echo ""
echo "🌐 Starting frontend server..."
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✨ Bottom is running!"
echo ""
echo "📊 Dashboard: http://localhost:8080"
echo "📡 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for user to stop
trap "echo ''; echo '🛑 Stopping Bottom...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait 