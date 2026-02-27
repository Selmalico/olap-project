#!/usr/bin/env python3
"""
Backend Diagnostics Script
Checks if all components are working correctly
"""

import sys
import time

print("=" * 70)
print("OLAP Analytics Backend - Diagnostic Check")
print("=" * 70)
print()

# Test 1: Check Python version
print("1️⃣  Checking Python version...")
python_version = (
    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
)
print(f"   Python: {python_version}")
if sys.version_info >= (3, 9):
    print("   ✅ Python version OK")
else:
    print("   ❌ Python 3.9+ required")
print()

# Test 2: Check imports
print("2️⃣  Checking imports...")
errors = []

try:
    import fastapi

    print(f"   ✅ FastAPI {fastapi.__version__}")
except ImportError as e:
    errors.append(f"FastAPI: {e}")
    print(f"   ❌ FastAPI: {e}")

try:
    import duckdb

    print(f"   ✅ DuckDB {duckdb.__version__}")
except ImportError as e:
    errors.append(f"DuckDB: {e}")
    print(f"   ❌ DuckDB: {e}")

try:
    import pandas

    print(f"   ✅ Pandas {pandas.__version__}")
except ImportError as e:
    errors.append(f"Pandas: {e}")
    print(f"   ❌ Pandas: {e}")

try:
    import anthropic

    print(f"   ✅ Anthropic")
except ImportError as e:
    errors.append(f"Anthropic: {e}")
    print(f"   ❌ Anthropic: {e}")

print()

# Test 3: Check agents
print("3️⃣  Checking agents...")
agent_errors = []

try:
    from agents.planner import PlannerAgent

    print("   ✅ PlannerAgent")
except Exception as e:
    agent_errors.append(f"PlannerAgent: {e}")
    print(f"   ❌ PlannerAgent: {e}")

try:
    from agents.anomaly_detection import AnomalyDetectionAgent

    print("   ✅ AnomalyDetectionAgent")
except Exception as e:
    agent_errors.append(f"AnomalyDetectionAgent: {e}")
    print(f"   ❌ AnomalyDetectionAgent: {e}")

try:
    from agents.executive_summary import ExecutiveSummaryAgent

    print("   ✅ ExecutiveSummaryAgent")
except Exception as e:
    agent_errors.append(f"ExecutiveSummaryAgent: {e}")
    print(f"   ❌ ExecutiveSummaryAgent: {e}")

try:
    from agents.visualization_agent import VisualizationAgent

    print("   ✅ VisualizationAgent")
except Exception as e:
    agent_errors.append(f"VisualizationAgent: {e}")
    print(f"   ❌ VisualizationAgent: {e}")

print()

# Test 4: Check database
print("4️⃣  Checking database...")
try:
    from pathlib import Path

    if Path("../data/sales_data.csv").exists():
        print("   ✅ CSV data file found")
    else:
        print("   ❌ CSV data file NOT found at ../data/sales_data.csv")
        print("      Run: python ../generate_dataset.py")
except Exception as e:
    print(f"   ❌ Error checking CSV: {e}")

try:
    from database.connection import get_db, init_db

    print("   ✅ Database module imported")

    # Try to get connection
    conn = get_db()
    print("   ✅ Database connection established")

    # Check if data is loaded
    try:
        count = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
        if count > 0:
            print(f"   ✅ Database loaded: {count:,} rows")
        else:
            print("   ⚠️  Database empty - will load on startup")
    except Exception as e:
        print(f"   ⚠️  Could not query database: {e}")

except Exception as e:
    print(f"   ❌ Database error: {e}")

print()

# Test 5: Check routers
print("5️⃣  Checking routers...")
try:
    from routers import query as query_router

    print("   ✅ Query router imported")
except Exception as e:
    print(f"   ❌ Query router: {e}")

try:
    from routers import olap as olap_router

    print("   ✅ OLAP router imported")
except Exception as e:
    print(f"   ❌ OLAP router: {e}")

print()

# Summary
print("=" * 70)
if not errors and not agent_errors:
    print("✅ ALL CHECKS PASSED - Backend is ready!")
    print()
    print("To start the backend, run:")
    print("   python main.py")
    print()
    print("Then access:")
    print("   API: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("   Health: http://localhost:8000/health")
else:
    print("❌ ISSUES FOUND:")
    if errors:
        print("\nDependency errors:")
        for err in errors:
            print(f"   - {err}")
    if agent_errors:
        print("\nAgent errors:")
        for err in agent_errors:
            print(f"   - {err}")
    print("\nFix these issues before starting the backend.")

print("=" * 70)
