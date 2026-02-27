@echo off
REM Quick diagnostic script to test backend startup

cd /d c:\Users\selma_3ct5ekw\Desktop\olap\olap-project

echo.
echo ========================================
echo Backend Diagnostic Test
echo ========================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run run_project.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Checking Python dependencies...
python -m pip list | find "fastapi"

echo.
echo Checking DuckDB database...
python -c "import duckdb; print(f'DuckDB version: {duckdb.__version__}')"

echo.
echo Starting backend server...
echo If you see "Uvicorn running on http://127.0.0.1:8000" then backend is working!
echo.

cd backend
python main.py
