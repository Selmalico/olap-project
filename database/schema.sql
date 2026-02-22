-- DuckDB Star Schema
-- Run: duckdb database/olap.db < database/schema.sql

INSTALL httpfs;
LOAD httpfs;
SET s3_region='eu-central-1';

CREATE TABLE IF NOT EXISTS dim_date AS
SELECT DISTINCT
    year*10000 + month*100 + 1 as date_key,
    year, quarter, month, month_name, week
FROM read_parquet('s3://olap-bi-data/parquet/fact_sales.parquet');

CREATE TABLE IF NOT EXISTS dim_geography AS
SELECT DISTINCT
    ROW_NUMBER() OVER(ORDER BY region, country) as geo_key,
    region, country
FROM read_parquet('s3://olap-bi-data/parquet/fact_sales.parquet');

CREATE TABLE IF NOT EXISTS dim_product AS
SELECT DISTINCT
    ROW_NUMBER() OVER(ORDER BY category, subcategory) as product_key,
    category, subcategory
FROM read_parquet('s3://olap-bi-data/parquet/fact_sales.parquet');

CREATE TABLE IF NOT EXISTS dim_customer AS
SELECT DISTINCT
    ROW_NUMBER() OVER(ORDER BY customer_segment) as customer_key,
    customer_segment as segment
FROM read_parquet('s3://olap-bi-data/parquet/fact_sales.parquet');

CREATE VIEW IF NOT EXISTS fact_sales AS
SELECT f.*, g.geo_key, p.product_key, d.date_key, c.customer_key
FROM read_parquet('s3://olap-bi-data/parquet/fact_sales.parquet') f
LEFT JOIN dim_geography g USING (region, country)
LEFT JOIN dim_product p USING (category, subcategory)
LEFT JOIN dim_date d USING (year, quarter, month)
LEFT JOIN dim_customer c ON f.customer_segment = c.segment;
