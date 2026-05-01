@echo off
echo ==============================================
echo 🌿 Starting Solace Mental Health Journal 🌿
echo ==============================================

cd backend

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

echo Starting backend server on http://localhost:8000 ...
start "Solace Backend" cmd /c "uvicorn app:app --reload --port 8000"

cd ..\frontend
echo Starting frontend server on http://localhost:3000 ...
start "Solace Frontend Server" cmd /c "python -m http.server 3000"

echo Opening Solace Frontend in your default browser...
start http://localhost:3000

echo Done! The app is now fully running on localhost.
