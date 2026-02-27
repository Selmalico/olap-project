"""
Data Access Layer — SalesRepository
─────────────────────────────────────
Single source of truth for all SQL queries against the star-schema DuckDB database.
Agents must NOT import get_db() or write raw SQL directly.

All SQL helpers (BASE_JOIN, VALID_DIMENSIONS, _col, _where, _measure_expr) live here
and are re-exported so agents can use them for validation without touching the DB.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from database.connection import get_db


# ── SQL Constants ─────────────────────────────────────────────────────────────

BASE_JOIN = """
FROM fact_sales fs
JOIN dim_date      dd ON fs.date_id     = dd.date_id
JOIN dim_geography dg ON fs.geo_id      = dg.geo_id
JOIN dim_product   dp ON fs.product_id  = dp.product_id
JOIN dim_customer  dc ON fs.customer_id = dc.customer_id
"""

# Superset of all dimension columns referenced by any agent
VALID_DIMENSIONS: dict[str, str] = {
    "year":             "dd.year",
    "quarter":          "dd.quarter",
    "month":            "dd.month",
    "month_name":       "dd.month_name",
    "region":           "dg.region",
    "country":          "dg.country",
    "category":         "dp.category",
    "subcategory":      "dp.subcategory",
    "customer_segment": "dc.customer_segment",
}

VALID_MEASURES: set[str] = {"revenue", "profit", "cost", "quantity", "profit_margin"}


# ── SQL Helpers ───────────────────────────────────────────────────────────────

def _col(dim: str) -> str:
    """Resolve a logical dimension name to its fully-qualified SQL column."""
    return VALID_DIMENSIONS.get(dim, dim)


def _where(filters: dict[str, Any]) -> tuple[str, list]:
    """
    Convert a filter dict into a parameterized SQL WHERE clause.
    Returns (clause_string, params_list).
    Skips keys not in VALID_DIMENSIONS (safe - no injection path).
    Uses ? placeholders; pass the returned params list to execute().
    """
    clauses: list[str] = []
    params: list = []
    for k, v in (filters or {}).items():
        col = VALID_DIMENSIONS.get(k)
        if not col:
            continue
        if isinstance(v, list):
            placeholders = ", ".join("?" * len(v))
            clauses.append(f"{col} IN ({placeholders})")
            params.extend(v)
        elif isinstance(v, (int, float)):
            clauses.append(f"{col} = ?")
            params.append(v)
        else:
            clauses.append(f"{col} = ?")
            params.append(str(v))
    clause_str = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return clause_str, params


def _measure_expr(measure: str) -> str:
    """Return the SQL aggregate expression for a measure."""
    if measure == "profit_margin":
        return "AVG(fs.profit_margin)"
    return f"SUM(fs.{measure})"


# ── Repository Class ──────────────────────────────────────────────────────────

class SalesRepository:
    """
    Data Access Layer for the fact_sales star schema.

    All database calls are centralised here.
    Agents call these methods instead of constructing and executing SQL directly.
    """

    # ── KPI Calculator queries ────────────────────────────────────────────────

    def get_yoy_data(
        self,
        measure: str = "revenue",
        group_by: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Return yearly metric values, optionally broken down by a dimension.
        Used by KPICalculatorAgent.yoy_growth().
        """
        measure_col = _measure_expr(measure)
        dim_select  = f", {_col(group_by)} AS group_dim" if group_by else ""
        dim_group   = f", {_col(group_by)}" if group_by else ""
        where, params = _where(filters or {})

        sql = f"""
        SELECT dd.year {dim_select},
               {measure_col} AS metric
        {BASE_JOIN}
        {where}
        GROUP BY dd.year {dim_group}
        ORDER BY dd.year {dim_group}
        """
        return get_db().execute(sql, params).df()

    def get_mom_data(
        self,
        measure: str = "revenue",
        year: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Return monthly metric values.
        Used by KPICalculatorAgent.mom_change().
        """
        measure_col    = _measure_expr(measure)
        extra_filter   = {"year": year} if year else {}
        merged_filters = {**(filters or {}), **extra_filter}
        where, params = _where(merged_filters)

        sql = f"""
        SELECT dd.year, dd.month, dd.month_name,
               {measure_col} AS metric
        {BASE_JOIN}
        {where}
        GROUP BY dd.year, dd.month, dd.month_name
        ORDER BY dd.year, dd.month
        """
        return get_db().execute(sql, params).df()

    def get_profit_margins(
        self,
        group_by: str = "category",
        filters: dict[str, Any] | None = None,
        sort_desc: bool = True,
    ) -> pd.DataFrame:
        """
        Return profit margin breakdown by a dimension.
        Used by KPICalculatorAgent.profit_margins().
        """
        where, params = _where(filters or {})
        order = "DESC" if sort_desc else "ASC"

        sql = f"""
        SELECT {_col(group_by)} AS group_dim,
               SUM(fs.revenue)       AS total_revenue,
               SUM(fs.profit)        AS total_profit,
               AVG(fs.profit_margin) AS avg_margin,
               MIN(fs.profit_margin) AS min_margin,
               MAX(fs.profit_margin) AS max_margin,
               COUNT(*)              AS order_count
        {BASE_JOIN}
        {where}
        GROUP BY {_col(group_by)}
        ORDER BY avg_margin {order}
        """
        return get_db().execute(sql, params).df()

    def get_top_n(
        self,
        measure: str = "revenue",
        n: int = 5,
        group_by: str = "country",
        filters: dict[str, Any] | None = None,
        ascending: bool = False,
    ) -> pd.DataFrame:
        """
        Return top (or bottom) N values for a measure grouped by a dimension.
        Used by KPICalculatorAgent.top_n().
        """
        measure_col = _measure_expr(measure)
        where, params = _where(filters or {})
        order       = "ASC" if ascending else "DESC"

        sql = f"""
        SELECT {_col(group_by)} AS group_dim,
               {measure_col} AS metric,
               COUNT(*) AS order_count
        {BASE_JOIN}
        {where}
        GROUP BY {_col(group_by)}
        ORDER BY metric {order}
        LIMIT {n}
        """
        return get_db().execute(sql, params).df()

    def get_period_data(
        self,
        filters: dict[str, Any],
        measure: str = "revenue",
        group_by: str | None = None,
    ) -> pd.DataFrame:
        """
        Return aggregate measure for a given filter set (one period).
        Used by KPICalculatorAgent.compare_periods() for period_a and period_b.
        """
        where, params = _where(filters)
        measure_col = _measure_expr(measure)
        dim_select  = f", {_col(group_by)} AS group_dim" if group_by else ""
        dim_group   = f", {_col(group_by)}" if group_by else ""

        sql = f"""
        SELECT {measure_col} AS metric {dim_select}
        {BASE_JOIN}
        {where}
        GROUP BY 1=1 {dim_group}
        """
        return get_db().execute(sql, params).df()

    def get_revenue_share(
        self,
        group_by: str = "region",
        filters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Return each group's revenue and percentage share of total.
        Used by KPICalculatorAgent.revenue_share().
        """
        where, params = _where(filters or {})

        sql = f"""
        WITH totals AS (
            SELECT {_col(group_by)} AS group_dim,
                   SUM(fs.revenue) AS group_revenue
            {BASE_JOIN}
            {where}
            GROUP BY {_col(group_by)}
        ),
        grand AS (SELECT SUM(group_revenue) AS grand_total FROM totals)
        SELECT t.group_dim,
               t.group_revenue,
               ROUND(t.group_revenue / g.grand_total * 100, 2) AS revenue_share_pct
        FROM totals t, grand g
        ORDER BY t.group_revenue DESC
        """
        return get_db().execute(sql, params).df()

    # ── Cube Operations queries ───────────────────────────────────────────────

    def get_slice(
        self,
        dimension: str,
        value: Any,
        group_by: list[str],
        measures: list[str],
    ) -> pd.DataFrame:
        """
        Return aggregated measures filtered to a single dimension value.
        Used by CubeOperationsAgent.slice().
        """
        select_parts: list[str] = []
        if group_by:
            select_parts.append(
                ", ".join(_col(g) + f" AS {g}" for g in group_by)
            )
        select_parts.append(
            ", ".join(f"{_measure_expr(m)} AS total_{m}" for m in measures)
        )
        select_dims_measures = ", ".join(p for p in select_parts if p)

        group_clause = ("GROUP BY " + ", ".join(_col(g) for g in group_by)) if group_by else ""
        order_clause = ("ORDER BY " + ", ".join(_col(g) for g in group_by)) if group_by else ""
        where, params = _where({dimension: value})

        sql = f"""
        SELECT {select_dims_measures},
               COUNT(*) AS order_count
        {BASE_JOIN}
        {where}
        {group_clause}
        {order_clause}
        """
        return get_db().execute(sql, params).df()

    def get_dice(
        self,
        filters: dict[str, Any],
        group_by: list[str],
        measures: list[str],
    ) -> pd.DataFrame:
        """
        Return aggregated measures with multiple dimension filters applied.
        Used by CubeOperationsAgent.dice().
        """
        select_parts: list[str] = []
        if group_by:
            select_parts.append(
                ", ".join(_col(g) + f" AS {g}" for g in group_by)
            )
        select_parts.append(
            ", ".join(f"{_measure_expr(m)} AS total_{m}" for m in measures)
        )
        select_dims_measures = ", ".join(p for p in select_parts if p)

        group_clause = ("GROUP BY " + ", ".join(_col(g) for g in group_by)) if group_by else ""
        order_clause = ("ORDER BY " + ", ".join(_col(g) for g in group_by)) if group_by else ""
        where, params = _where(filters)

        sql = f"""
        SELECT {select_dims_measures},
               COUNT(*) AS order_count
        {BASE_JOIN}
        {where}
        {group_clause}
        {order_clause}
        """
        return get_db().execute(sql, params).df()

    def get_pivot_data(
        self,
        rows: str,
        columns: str,
        values: str,
        filters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Return raw row × column × value data for pivot construction.
        Used by CubeOperationsAgent.pivot().
        """
        where, params = _where(filters or {})
        measure_expr = _measure_expr(values)

        sql = f"""
        SELECT {_col(rows)} AS row_dim,
               {_col(columns)} AS col_dim,
               {measure_expr} AS val
        {BASE_JOIN}
        {where}
        GROUP BY {_col(rows)}, {_col(columns)}
        ORDER BY {_col(rows)}, {_col(columns)}
        """
        return get_db().execute(sql, params).df()

    def get_dimension_values(self, dimension: str) -> list:
        """
        Return all distinct values for a dimension.
        Used by CubeOperationsAgent.get_dimension_values().
        """
        col = _col(dimension)
        sql = f"""
        SELECT DISTINCT {col} AS value
        {BASE_JOIN}
        ORDER BY {col}
        """
        return [r[0] for r in get_db().execute(sql, []).fetchall()]

    # ── Dimension Navigator queries ───────────────────────────────────────────

    def get_hierarchy_data(
        self,
        group_cols: str,
        where_clause: str,
        order_by: str,
        params: list | None = None,
    ) -> pd.DataFrame:
        """
        Return aggregated sales data at a given hierarchy level.
        Used by DimensionNavigatorAgent.drill_down() and .roll_up().

        Parameters
        ----------
        group_cols  : SQL column expression, e.g. 'dd.year, dd.quarter'
        where_clause: pre-built WHERE string from _build_where()
        order_by    : SQL ORDER BY expression (typically same as group_cols)
        """
        sql = f"""
        SELECT {group_cols},
               SUM(fs.revenue)       AS total_revenue,
               SUM(fs.profit)        AS total_profit,
               SUM(fs.quantity)      AS total_quantity,
               COUNT(*)              AS order_count,
               AVG(fs.profit_margin) AS avg_margin
        {BASE_JOIN}
        {where_clause}
        GROUP BY {group_cols}
        ORDER BY {order_by}
        """
        return get_db().execute(sql, params or []).df()

    # ── Generic SQL execution helper ─────────────────────────────────────────

    def _execute(self, sql: str, params: list | None = None) -> pd.DataFrame:
        """Execute arbitrary parameterized SQL and return a DataFrame."""
        return get_db().execute(sql, params or []).df()

    # ── Generic aggregation ───────────────────────────────────────────────────

    def get_aggregate_data(
        self,
        aggregations: dict[str, str],
        group_by: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Execute a flexible aggregation query with caller-specified functions.

        Parameters
        ----------
        aggregations : mapping of output column name -> SQL expression, e.g.
                       {"total_revenue": "SUM(fs.revenue)",
                        "avg_margin":    "AVG(fs.profit_margin)",
                        "order_count":   "COUNT(*)"}
        group_by     : list of dimension names to GROUP BY
        filters      : dimension filter dict passed through _where()
        """
        agg_select = ", ".join(f"{expr} AS {alias}" for alias, expr in aggregations.items())
        dim_select  = (", ".join(_col(g) + f" AS {g}" for g in (group_by or [])))
        select_part = f"{dim_select}, {agg_select}" if dim_select else agg_select

        group_clause = ("GROUP BY " + ", ".join(_col(g) for g in group_by)) if group_by else ""
        order_clause = ("ORDER BY " + ", ".join(_col(g) for g in group_by)) if group_by else ""
        where, params = _where(filters or {})

        sql = f"""
        SELECT {select_part}
        {BASE_JOIN}
        {where}
        {group_clause}
        {order_clause}
        """
        return get_db().execute(sql, params).df()

    # ── Report Generator (dashboard cards) ───────────────────────────────────

    def get_dashboard_totals(self) -> tuple:
        """
        Return a single aggregate row for the dashboard overview cards.
        Used by ReportGeneratorAgent.dashboard_cards().
        """
        sql = """
        SELECT
            SUM(fs.revenue)            AS total_revenue,
            SUM(fs.profit)             AS total_profit,
            AVG(fs.profit_margin)      AS avg_margin,
            SUM(fs.quantity)           AS total_quantity,
            COUNT(*)                   AS total_orders,
            COUNT(DISTINCT dg.country) AS countries,
            MIN(dd.year)               AS min_year,
            MAX(dd.year)               AS max_year
        FROM fact_sales fs
        JOIN dim_date      dd ON fs.date_id = dd.date_id
        JOIN dim_geography dg ON fs.geo_id  = dg.geo_id
        """
        return get_db().execute(sql).fetchone()
