# OLAP BI Platform — Backend (FastAPI + DuckDB)
# For Render / Railway / Fly.io
# Build context: repo root (render.yaml uses dockerfilePath: ./backend/Dockerfile)

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source and data scripts
COPY backend/ ./backend/
COPY data/ ./data/

# Generate sales_data.csv (integer quarter) for star-schema loader
RUN python /app/data/generate_dataset.py

# Data and DB paths (DuckDB file created at startup from CSV)
ENV DATABASE_PATH=/app/data/olap.duckdb
ENV CSV_PATH=/app/data/sales_data.csv
ENV PORT=8000

WORKDIR /app/backend

EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
