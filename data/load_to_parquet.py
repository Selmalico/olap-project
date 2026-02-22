import duckdb
import boto3
import os

con = duckdb.connect()

con.execute("""
    CREATE TABLE fact_sales AS
    SELECT
        ROW_NUMBER() OVER() as fact_id,
        CAST(order_date AS DATE) as order_date,
        year, quarter, month, month_name, week,
        region, country, category, subcategory,
        customer_segment, quantity, unit_price,
        revenue, cost, profit, profit_margin
    FROM read_csv_auto('data/raw/global_retail_sales.csv')
""")

os.makedirs("data/parquet", exist_ok=True)
con.execute("COPY fact_sales TO 'data/parquet/fact_sales.parquet' (FORMAT PARQUET)")
print("Created data/parquet/fact_sales.parquet")

s3 = boto3.client('s3')
s3.upload_file(
    'data/parquet/fact_sales.parquet',
    'olap-bi-data',
    'parquet/fact_sales.parquet'
)
print("Uploaded -> s3://olap-bi-data/parquet/fact_sales.parquet")
