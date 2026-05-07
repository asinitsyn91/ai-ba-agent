#!/bin/bash
# AI-ba-agent startup script
set -e

cd "$(dirname "$0")"

echo "=== AI-ba-agent ==="

# Backend
cd backend
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
echo "Installing dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  echo "WARNING: .env not found. Copying from .env.example"
  cp .env.example .env
fi

echo "Starting backend on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

cd ../frontend
echo "Starting frontend on port 3000..."
python3 -m http.server 3000 --directory public &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ Running:"
echo "   Backend API: http://localhost:8000"
echo "   Frontend:    http://localhost:3000"
echo "   API Docs:    http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
