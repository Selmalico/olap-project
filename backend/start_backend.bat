@echo off
REM Quick start with diagnostics

cd /d c:\Users\selma_3ct5ekw\Desktop\olap\olap-project\backend

echo.
echo ════════════════════════════════════════════════════════════════
echo                    Backend Diagnostics Check
echo ════════════════════════════════════════════════════════════════
echo.

call .venv\Scripts\activate.bat

echo Running diagnostics...
python diagnostics.py

echo.
echo ════════════════════════════════════════════════════════════════
echo                    Starting Backend Server
echo ════════════════════════════════════════════════════════════════
echo.
echo Backend will start and respond immediately.
echo Database loads in the background.
echo.
echo Test endpoints:
echo   http://localhost:8000/health
echo   http://localhost:8000/docs
echo   http://localhost:8000/api/query/dashboard
echo.
echo Press Ctrl+C to stop.
echo.

python main.py
