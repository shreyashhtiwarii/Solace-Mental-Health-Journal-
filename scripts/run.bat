@echo off
echo ==============================================
echo 🌿 Starting Solace Mental Health Journal 🌿
echo ==============================================

cd /d "%~dp0..\backend"

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Starting backend server on http://localhost:8000 ...
start "Solace Backend" cmd /k "venv\Scripts\python.exe -m uvicorn app:app --reload --port 8000"

cd /d "%~dp0..\frontend"
echo Starting frontend server on http://localhost:3000 ...
start "Solace Frontend Server" cmd /k "python -m http.server 3000"

echo Opening Solace Frontend in your default browser...
start http://localhost:3000

echo Done! The app is now fully running on localhost.
