"""
DuckDB connection manager and star-schema initialiser.

Star schema:
    fact_sales  ─┬─ dim_date
                 ├─ dim_geography
                 ├─ dim_product
                 └─ dim_customer
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

_DB_PATH = os.getenv("DATABASE_PATH", "../data/olap.duckdb")
_CSV_PATH = os.getenv("CSV_PATH", "../data/sales_data.csv")

_lock = threading.Lock()
_conn: duckdb.DuckDBPyConnection | None = None


def get_db() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        with _lock:
            if _conn is None:
                _conn = duckdb.connect(_DB_PATH, read_only=False)
    return _conn


DDL = """
CREATE TABLE IF NOT EXISTS dim_date (
    date_id   INTEGER PRIMARY KEY,
    order_date DATE,
    year       INTEGER,
    quarter    INTEGER,
    month      INTEGER,
    month_name VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_geography (
    geo_id  INTEGER PRIMARY KEY,
    region  VARCHAR,
    country VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id  INTEGER PRIMARY KEY,
    category    VARCHAR,
    subcategory VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id      INTEGER PRIMARY KEY,
    customer_segment VARCHAR
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id       INTEGER PRIMARY KEY,
    order_id      VARCHAR,
    date_id       INTEGER REFERENCES dim_date(date_id),
    geo_id        INTEGER REFERENCES dim_geography(geo_id),
    product_id    INTEGER REFERENCES dim_product(product_id),
    customer_id   INTEGER REFERENCES dim_customer(customer_id),
    quantity      INTEGER,
    unit_price    DOUBLE,
    revenue       DOUBLE,
    cost          DOUBLE,
    profit        DOUBLE,
    profit_margin DOUBLE
);
"""


def _load_csv_to_star_schema(conn: duckdb.DuckDBPyConnection, csv_path: str) -> None:
    """Read the flat CSV and populate the normalised star schema."""
    df = pd.read_csv(csv_path, parse_dates=["order_date"])

    # ── dim_date ──────────────────────────────────────────────
    dates = (
        df[["order_date", "year", "quarter", "month", "month_name"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dates.insert(0, "date_id", range(1, len(dates) + 1))
    conn.execute("DELETE FROM dim_date")
    conn.register("_dates", dates)
    conn.execute("INSERT INTO dim_date SELECT * FROM _dates")

    # ── dim_geography ─────────────────────────────────────────
    geos = (
        df[["region", "country"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    geos.insert(0, "geo_id", range(1, len(geos) + 1))
    conn.execute("DELETE FROM dim_geography")
    conn.register("_geos", geos)
    conn.execute("INSERT INTO dim_geography SELECT * FROM _geos")

    # ── dim_product ───────────────────────────────────────────
    products = (
        df[["category", "subcategory"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    products.insert(0, "product_id", range(1, len(products) + 1))
    conn.execute("DELETE FROM dim_product")
    conn.register("_products", products)
    conn.execute("INSERT INTO dim_product SELECT * FROM _products")

    # ── dim_customer ──────────────────────────────────────────
    customers = (
        df[["customer_segment"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    customers.insert(0, "customer_id", range(1, len(customers) + 1))
    conn.execute("DELETE FROM dim_customer")
    conn.register("_customers", customers)
    conn.execute("INSERT INTO dim_customer SELECT * FROM _customers")

    # ── fact_sales ────────────────────────────────────────────
    df2 = df.merge(dates[["date_id", "order_date", "year", "quarter", "month", "month_name"]],
                   on=["order_date", "year", "quarter", "month", "month_name"])
    df2 = df2.merge(geos, on=["region", "country"])
    df2 = df2.merge(products, on=["category", "subcategory"])
    df2 = df2.merge(customers, on="customer_segment")

    fact = df2[["order_id", "date_id", "geo_id", "product_id", "customer_id",
                "quantity", "unit_price", "revenue", "cost", "profit", "profit_margin"]].copy()
    fact.insert(0, "sale_id", range(1, len(fact) + 1))

    conn.execute("DELETE FROM fact_sales")
    conn.register("_fact", fact)
    conn.execute("INSERT INTO fact_sales SELECT * FROM _fact")

    row_count = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    print(f"[OK] Star schema loaded: {row_count:,} fact rows")


def init_db() -> None:
    """Create schema tables and load data from CSV if not already done."""
    conn = get_db()
    conn.execute(DDL)

    row_count = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    if row_count == 0:
        csv_path = Path(_CSV_PATH)
        if not csv_path.exists():
            raise FileNotFoundError(
                f"CSV not found at '{csv_path}'. Run `python generate_dataset.py` first."
            )
        _load_csv_to_star_schema(conn, str(csv_path))
    else:
        print(f"[OK] Database ready: {row_count:,} fact rows")
