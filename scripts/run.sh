#!/bin/bash
echo "=============================================="
echo "🌿 Starting Solace Mental Health Journal 🌿"
echo "=============================================="

cd ../backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
pip install -r requirements.txt

echo "Starting backend server on http://localhost:8000 ..."
# Start uvicorn in the background
uvicorn app:app --reload --port 8000 &

cd ../frontend
echo "Starting frontend server on http://localhost:3000 ..."
# Start simple http server for frontend in the background
python -m http.server 3000 &

echo "Opening Solace Frontend in your default browser..."
# Use start for Windows (Git Bash), open for Mac, xdg-open for Linux
if command -v start > /dev/null; then
    start http://localhost:3000
elif command -v open > /dev/null; then
    open http://localhost:3000
elif command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
fi

echo "Done! The app is now fully running on localhost."
wait
