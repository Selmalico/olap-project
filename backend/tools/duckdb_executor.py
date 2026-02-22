import duckdb
from config import settings


def get_connection():
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='{settings.aws_region}';")
    return con


def execute_query(sql: str) -> list:
    """Execute SQL against DuckDB/S3 and return list of dicts."""
    con = get_connection()
    try:
        result = con.execute(sql).fetchdf()
        return result.to_dict(orient="records")
    except Exception as e:
        raise ValueError(f"SQL Error: {str(e)}\nSQL: {sql}")
    finally:
        con.close()


def get_schema_info() -> dict:
    """Return schema metadata for injection into agent prompts."""
    s3_path = f"s3://{settings.s3_data_bucket}/parquet/fact_sales.parquet"
    return {
        "fact_table": "fact_sales",
        "s3_path": s3_path,
        "dimensions": [
            "region", "country", "category", "subcategory",
            "customer_segment", "year", "quarter", "month", "month_name", "week"
        ],
        "measures": ["quantity", "unit_price", "revenue", "cost", "profit", "profit_margin"],
        "date_range": "2022-2024",
        "total_rows": 10000,
        "sql_prefix": f"FROM read_parquet('{s3_path}') AS f"
    }
