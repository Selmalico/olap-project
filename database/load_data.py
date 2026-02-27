"""
OLAP Analytics — Standalone Data Loading Script
===============================================
Transforms the flat CSV (data/sales_data.csv) into the normalised star schema
and persists it to a DuckDB file (data/olap.duckdb).

Steps
-----
1. Read flat CSV                       → pandas DataFrame
2. Extract dim_date                    → deduplicated date rows
3. Extract dim_geography               → deduplicated region/country rows
4. Extract dim_product                 → deduplicated category/subcategory rows
5. Extract dim_customer                → deduplicated customer_segment rows
6. Build fact_sales                    → merge FKs back onto raw rows
7. Execute DDL (schema.sql)            → create tables if absent
8. Load each table in FK-safe order    → dimensions first, fact last
9. Print row counts for verification

Usage
-----
    # From the project root:
    python database/load_data.py

    # Or with custom paths:
    python database/load_data.py \
        --csv   data/sales_data.csv \
        --db    data/olap.duckdb \
        --ddl   database/schema.sql

Prerequisites
-------------
    pip install duckdb pandas
    python generate_dataset.py          # only if CSV does not exist yet
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import pandas as pd

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _banner(text: str) -> None:
    print(f"\n{'-' * 60}")
    print(f"  {text}")
    print(f"{'-' * 60}")


def _check(text: str) -> None:
    print(f"  [OK] {text}")


def _fail(text: str) -> None:
    print(f"  [FAIL] {text}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Extract dimension DataFrames from the flat CSV
# ---------------------------------------------------------------------------


def extract_dimensions(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Derive the four dimension tables from the flat source DataFrame.

    Returns a dict:
        "dim_date"      → DataFrame with surrogate key + date attributes
        "dim_geography" → DataFrame with surrogate key + region, country
        "dim_product"   → DataFrame with surrogate key + category, subcategory
        "dim_customer"  → DataFrame with surrogate key + customer_segment
    """
    # ── dim_date ──────────────────────────────────────────────────────────
    dim_date = (
        df[["order_date", "year", "quarter", "month", "month_name"]]
        .drop_duplicates()
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )
    dim_date.insert(0, "date_id", range(1, len(dim_date) + 1))

    # ── dim_geography ─────────────────────────────────────────────────────
    dim_geography = (
        df[["region", "country"]]
        .drop_duplicates()
        .sort_values(["region", "country"])
        .reset_index(drop=True)
    )
    dim_geography.insert(0, "geo_id", range(1, len(dim_geography) + 1))

    # ── dim_product ───────────────────────────────────────────────────────
    dim_product = (
        df[["category", "subcategory"]]
        .drop_duplicates()
        .sort_values(["category", "subcategory"])
        .reset_index(drop=True)
    )
    dim_product.insert(0, "product_id", range(1, len(dim_product) + 1))

    # ── dim_customer ──────────────────────────────────────────────────────
    dim_customer = (
        df[["customer_segment"]]
        .drop_duplicates()
        .sort_values("customer_segment")
        .reset_index(drop=True)
    )
    dim_customer.insert(0, "customer_id", range(1, len(dim_customer) + 1))

    return {
        "dim_date": dim_date,
        "dim_geography": dim_geography,
        "dim_product": dim_product,
        "dim_customer": dim_customer,
    }


# ---------------------------------------------------------------------------
# Build fact table by joining FK surrogate keys back onto raw rows
# ---------------------------------------------------------------------------


def build_fact_sales(df: pd.DataFrame, dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Join the four dimension tables onto the flat DataFrame to obtain FK columns,
    then select only the fact columns for fact_sales.

    Parameters
    ----------
    df   : original flat CSV DataFrame
    dims : output of extract_dimensions()

    Returns
    -------
    fact_sales DataFrame ready for loading
    """
    fact = df.copy()

    # Merge date FK
    fact = fact.merge(
        dims["dim_date"][
            ["date_id", "order_date", "year", "quarter", "month", "month_name"]
        ],
        on=["order_date", "year", "quarter", "month", "month_name"],
    )

    # Merge geography FK
    fact = fact.merge(
        dims["dim_geography"],
        on=["region", "country"],
    )

    # Merge product FK
    fact = fact.merge(
        dims["dim_product"],
        on=["category", "subcategory"],
    )

    # Merge customer FK
    fact = fact.merge(
        dims["dim_customer"],
        on="customer_segment",
    )

    # Select and order fact columns only
    fact = fact[
        [
            "order_id",
            "date_id",
            "geo_id",
            "product_id",
            "customer_id",
            "quantity",
            "unit_price",
            "revenue",
            "cost",
            "profit",
            "profit_margin",
        ]
    ].copy()
    fact.insert(0, "sale_id", range(1, len(fact) + 1))

    return fact


# ---------------------------------------------------------------------------
# Load a DataFrame into DuckDB, clearing the table first
# ---------------------------------------------------------------------------


def _load_table(
    conn: duckdb.DuckDBPyConnection, table_name: str, df: pd.DataFrame
) -> int:
    """Truncate *table_name* and bulk-insert *df*. Returns row count."""
    conn.execute(f"DELETE FROM {table_name}")
    conn.register(f"_src_{table_name}", df)
    conn.execute(f"INSERT INTO {table_name} SELECT * FROM _src_{table_name}")
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return count


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def load(csv_path: str, db_path: str, ddl_path: str) -> None:
    """
    Full ETL pipeline: CSV → star schema in DuckDB.

    Parameters
    ----------
    csv_path : path to the flat CSV file
    db_path  : path to the DuckDB database file (created if absent)
    ddl_path : path to the DDL SQL file (schema.sql)
    """
    _banner("OLAP Analytics - Data Loading Script")

    # ── 1. Validate inputs ────────────────────────────────────────────────
    csv_file = Path(csv_path)
    ddl_file = Path(ddl_path)

    if not csv_file.exists():
        _fail(
            f"CSV not found: {csv_file}\n       Run `python generate_dataset.py` first."
        )
    if not ddl_file.exists():
        _fail(f"DDL file not found: {ddl_file}")

    print(f"\n  CSV source : {csv_file.resolve()}")
    print(f"  DuckDB file: {Path(db_path).resolve()}")
    print(f"  DDL file   : {ddl_file.resolve()}")

    # ── 2. Read CSV ───────────────────────────────────────────────────────
    print("\n[1/5] Reading CSV …")
    df = pd.read_csv(csv_file, parse_dates=["order_date"])
    _check(f"{len(df):,} raw rows  ·  {len(df.columns)} columns")

    # ── 3. Extract dimensions ─────────────────────────────────────────────
    print("\n[2/5] Extracting dimension tables …")
    dims = extract_dimensions(df)
    for name, dim_df in dims.items():
        _check(f"{name:<18}  {len(dim_df):>4} rows")

    # ── 4. Build fact table ───────────────────────────────────────────────
    print("\n[3/5] Building fact_sales …")
    fact = build_fact_sales(df, dims)
    _check(f"fact_sales          {len(fact):>6} rows  ·  {len(fact.columns)} columns")

    # ── 5. Connect to DuckDB and apply DDL ────────────────────────────────
    print("\n[4/5] Applying DDL to DuckDB …")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(db_path, read_only=False)
    ddl_sql = ddl_file.read_text(encoding="utf-8")
    conn.execute(ddl_sql)
    _check("Schema created / verified")

    # ── 6. Load tables (FK-safe order: dimensions first, fact last) ───────
    print("\n[5/5] Loading tables …")
    load_order = [
        ("dim_date", dims["dim_date"]),
        ("dim_geography", dims["dim_geography"]),
        ("dim_product", dims["dim_product"]),
        ("dim_customer", dims["dim_customer"]),
        ("fact_sales", fact),
    ]
    for table_name, table_df in load_order:
        count = _load_table(conn, table_name, table_df)
        _check(f"{table_name:<18}  {count:>6} rows loaded")

    conn.close()

    # ── 7. Verification summary ───────────────────────────────────────────
    _banner("Load complete — Verification")
    conn_verify = duckdb.connect(db_path, read_only=True)
    tables = ["dim_date", "dim_geography", "dim_product", "dim_customer", "fact_sales"]
    for t in tables:
        n = conn_verify.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<20}  {n:>6} rows")
    conn_verify.close()
    print()


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    # Default paths relative to the project root (one level above database/)
    script_dir = Path(__file__).resolve().parent  # database/
    project_root = script_dir.parent  # olap-project/

    parser = argparse.ArgumentParser(
        description="Load flat CSV into the star-schema DuckDB database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--csv",
        default=str(project_root / "data" / "sales_data.csv"),
        help="Path to the flat source CSV file",
    )
    parser.add_argument(
        "--db",
        default=str(project_root / "data" / "olap.duckdb"),
        help="Path to the DuckDB database file",
    )
    parser.add_argument(
        "--ddl",
        default=str(script_dir / "schema.sql"),
        help="Path to the DDL SQL file",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    load(csv_path=args.csv, db_path=args.db, ddl_path=args.ddl)
