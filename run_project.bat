@echo off
REM OLAP Project Launcher - Backend and Frontend Setup
REM This script sets up and runs the complete OLAP BI platform

setlocal enabledelayedexpansion

cd /d c:\Users\selma_3ct5ekw\Desktop\olap\olap-project

echo.
echo ========================================
echo OLAP Project - Setup and Run
echo ========================================
echo.

REM Step 1: Check if virtual environment exists
if not exist ".venv" (
    echo [1/5] Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo [1/5] Virtual environment already exists.
)

echo.
echo [2/5] Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat

REM Upgrade pip to latest version
echo Upgrading pip...
python -m pip install --upgrade pip

REM Clear pip cache
pip cache purge

REM Install setuptools and wheel FIRST (required for Python 3.13)
echo Installing build tools (setuptools, wheel)...
pip install --upgrade setuptools wheel

REM Install backend dependencies (--only-binary :all: forces wheel-only, no source builds)
echo Installing backend dependencies (wheel-only mode)...
pip install --only-binary :all: -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    exit /b 1
)
echo Backend dependencies installed successfully.

echo.
echo [3/5] Generating dataset...
python generate_dataset.py
if errorlevel 1 (
    echo ERROR: Failed to generate dataset
    exit /b 1
)
echo Dataset generated successfully.

echo.
echo [4/5] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies
    cd ..
    exit /b 1
)
echo Frontend dependencies installed successfully.
cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Starting services...
echo - Backend will start on http://localhost:8000
echo - Frontend will start on http://localhost:5173
echo - API docs: http://localhost:8000/docs
echo.
echo Note: Both servers will run concurrently in separate terminal windows.
echo.
pause

REM Step 5: Start backend server
echo [5/5] Starting Backend Server...
start "OLAP Backend Server" cmd /k "cd /d c:\Users\selma_3ct5ekw\Desktop\olap\olap-project && call .venv\Scripts\activate.bat && cd backend && uvicorn main:app --reload --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak

REM Step 6: Start frontend server
echo Starting Frontend Server...
start "OLAP Frontend Server" cmd /k "cd /d c:\Users\selma_3ct5ekw\Desktop\olap\olap-project\frontend && npm run dev"

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Backend API:   http://localhost:8000
echo Frontend App:  http://localhost:5173
echo API Docs:      http://localhost:8000/docs
echo.
echo To stop servers:
echo - Close the backend window (Ctrl+C)
echo - Close the frontend window (Ctrl+C)
echo.
pause
