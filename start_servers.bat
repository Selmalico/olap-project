@echo off
REM Quick Start - For after initial setup
REM Just activates venv and starts both servers

cd /d c:\Users\selma_3ct5ekw\Desktop\olap\olap-project

echo.
echo ========================================
echo OLAP Project - Quick Start
echo ========================================
echo.
echo Starting Backend Server...
start "OLAP Backend" cmd /k "cd /d c:\Users\selma_3ct5ekw\Desktop\olap\olap-project && call .venv\Scripts\activate.bat && cd backend && uvicorn main:app --reload --port 8000"

timeout /t 2 /nobreak

echo Starting Frontend Server...
start "OLAP Frontend" cmd /k "cd /d c:\Users\selma_3ct5ekw\Desktop\olap\olap-project\frontend && npm run dev"

echo.
echo ========================================
echo Services Started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo Docs:     http://localhost:8000/docs
echo.
pause
