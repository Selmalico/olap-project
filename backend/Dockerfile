# OLAP BI Platform — Backend (FastAPI + DuckDB)
# For Render / Railway / Fly.io

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and data
COPY backend/ ./backend/
COPY data/ ./data/

# Generate sales_data.csv (integer quarter) for star-schema loader
RUN python data/generate_dataset.py

# Data and DB paths (DuckDB file created at startup)
ENV DATABASE_PATH=/app/data/olap.duckdb
ENV CSV_PATH=/app/data/sales_data.csv

WORKDIR /app/backend

# Render/Railway/Fly.io set PORT
ENV PORT=8000
EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
