#!/bin/bash
# Stop any backend on port 8000/8001 (frees the DuckDB lock so you can start fresh).

echo "Stopping processes on port 8000..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
echo "Stopping processes on port 8001..."
lsof -ti :8001 | xargs kill -9 2>/dev/null || true
echo "Done. From backend folder run: uvicorn main:app --reload --port 8000"
