"""
KPI Calculator Agent
─────────────────────
Computes business KPIs:
  • Year-over-Year (YoY) growth
  • Month-over-Month (MoM) change
  • Profit margins by dimension
  • Top-N rankings
  • Period comparisons
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from database.connection import get_db

BASE_JOIN = """
FROM fact_sales fs
JOIN dim_date      dd ON fs.date_id     = dd.date_id
JOIN dim_geography dg ON fs.geo_id      = dg.geo_id
JOIN dim_product   dp ON fs.product_id  = dp.product_id
JOIN dim_customer  dc ON fs.customer_id = dc.customer_id
"""

VALID_DIMENSIONS = {
    "year": "dd.year",
    "quarter": "dd.quarter",
    "month": "dd.month",
    "region": "dg.region",
    "country": "dg.country",
    "category": "dp.category",
    "subcategory": "dp.subcategory",
    "customer_segment": "dc.customer_segment",
}


def _col(dim: str) -> str:
    return VALID_DIMENSIONS.get(dim, dim)


def _where(filters: dict[str, Any]) -> str:
    clauses: list[str] = []
    for k, v in (filters or {}).items():
        col = VALID_DIMENSIONS.get(k)
        if not col:
            continue
        if isinstance(v, list):
            quoted = ", ".join(f"'{x}'" for x in v)
            clauses.append(f"{col} IN ({quoted})")
        elif isinstance(v, (int, float)):
            clauses.append(f"{col} = {v}")
        else:
            clauses.append(f"{col} = '{v}'")
    return ("WHERE " + " AND ".join(clauses)) if clauses else ""


class KPICalculatorAgent:
    """Calculates business KPIs from the star-schema data warehouse."""

    def yoy_growth(
        self,
        measure: str = "revenue",
        group_by: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Year-over-Year growth for a measure, optionally broken down by a dimension.

        Returns current year value, previous year value, absolute change, and % change.
        """
        if measure not in ("revenue", "profit", "cost", "quantity", "profit_margin"):
            return {"error": f"Invalid measure '{measure}'."}
        
        if group_by and group_by not in VALID_DIMENSIONS:
            return {"error": f"Invalid group_by dimension '{group_by}'. Valid: {list(VALID_DIMENSIONS.keys())}"}

        measure_col = f"SUM(fs.{measure})" if measure != "profit_margin" else "AVG(fs.profit_margin)"
        dim_select = f", {_col(group_by)} AS group_dim" if group_by else ""
        dim_group = f", {_col(group_by)}" if group_by else ""
        where = _where(filters or {})

        sql = f"""
        SELECT dd.year {dim_select},
               {measure_col} AS metric
        {BASE_JOIN}
        {where}
        GROUP BY dd.year {dim_group}
        ORDER BY dd.year {dim_group}
        """
        df = get_db().execute(sql).df()

        if group_by:
            result_rows = []
            for group_val, grp in df.groupby("group_dim"):
                grp = grp.sort_values("year")
                grp["prev_metric"] = grp["metric"].shift(1)
                grp["abs_change"] = grp["metric"] - grp["prev_metric"]
                grp["pct_change"] = (grp["abs_change"] / grp["prev_metric"] * 100).round(2)
                for _, row in grp.iterrows():
                    result_rows.append({
                        "group": group_val,
                        "year": int(row["year"]),
                        "current": round(row["metric"], 2),
                        "previous": round(row["prev_metric"], 2) if pd.notna(row["prev_metric"]) else None,
                        "abs_change": round(row["abs_change"], 2) if pd.notna(row["abs_change"]) else None,
                        "pct_change": row["pct_change"] if pd.notna(row["pct_change"]) else None,
                    })
            return {"operation": "yoy_growth", "measure": measure, "group_by": group_by, "rows": result_rows}
        else:
            df = df.sort_values("year")
            df["prev_metric"] = df["metric"].shift(1)
            df["abs_change"] = df["metric"] - df["prev_metric"]
            df["pct_change"] = (df["abs_change"] / df["prev_metric"] * 100).round(2)
            rows = []
            for _, row in df.iterrows():
                rows.append({
                    "year": int(row["year"]),
                    "current": round(row["metric"], 2),
                    "previous": round(row["prev_metric"], 2) if pd.notna(row["prev_metric"]) else None,
                    "abs_change": round(row["abs_change"], 2) if pd.notna(row["abs_change"]) else None,
                    "pct_change": row["pct_change"] if pd.notna(row["pct_change"]) else None,
                })
            return {"operation": "yoy_growth", "measure": measure, "group_by": None, "rows": rows}

    def mom_change(
        self,
        measure: str = "revenue",
        year: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Month-over-Month change for a given measure and optional year filter."""
        measure_col = f"SUM(fs.{measure})" if measure != "profit_margin" else "AVG(fs.profit_margin)"
        extra_filter = {}
        if year:
            extra_filter["year"] = year
        merged_filters = {**(filters or {}), **extra_filter}
        where = _where(merged_filters)

        sql = f"""
        SELECT dd.year, dd.month, dd.month_name,
               {measure_col} AS metric
        {BASE_JOIN}
        {where}
        GROUP BY dd.year, dd.month, dd.month_name
        ORDER BY dd.year, dd.month
        """
        df = get_db().execute(sql).df()
        df["prev_metric"] = df["metric"].shift(1)
        df["abs_change"] = df["metric"] - df["prev_metric"]
        df["pct_change"] = (df["abs_change"] / df["prev_metric"] * 100).round(2)

        rows = []
        for _, row in df.iterrows():
            rows.append({
                "year": int(row["year"]),
                "month": int(row["month"]),
                "month_name": row["month_name"],
                "current": round(row["metric"], 2),
                "previous": round(row["prev_metric"], 2) if pd.notna(row["prev_metric"]) else None,
                "abs_change": round(row["abs_change"], 2) if pd.notna(row["abs_change"]) else None,
                "pct_change": row["pct_change"] if pd.notna(row["pct_change"]) else None,
            })
        return {"operation": "mom_change", "measure": measure, "year": year, "rows": rows}

    def profit_margins(
        self,
        group_by: str = "category",
        filters: dict[str, Any] | None = None,
        sort_desc: bool = True,
    ) -> dict[str, Any]:
        """Return average profit margins broken down by a dimension."""
        if group_by not in VALID_DIMENSIONS:
            return {"error": f"Unknown dimension '{group_by}'."}
        where = _where(filters or {})
        order = "DESC" if sort_desc else "ASC"

        sql = f"""
        SELECT {_col(group_by)} AS group_dim,
               SUM(fs.revenue)           AS total_revenue,
               SUM(fs.profit)            AS total_profit,
               AVG(fs.profit_margin)     AS avg_margin,
               MIN(fs.profit_margin)     AS min_margin,
               MAX(fs.profit_margin)     AS max_margin,
               COUNT(*)                  AS order_count
        {BASE_JOIN}
        {where}
        GROUP BY {_col(group_by)}
        ORDER BY avg_margin {order}
        """
        df = get_db().execute(sql).df()
        return {
            "operation": "profit_margins",
            "group_by": group_by,
            "columns": list(df.columns),
            "rows": df.round(2).to_dict(orient="records"),
        }

    def top_n(
        self,
        measure: str = "revenue",
        n: int = 5,
        group_by: str = "country",
        filters: dict[str, Any] | None = None,
        ascending: bool = False,
    ) -> dict[str, Any]:
        """Return the top (or bottom) N values for a measure grouped by a dimension."""
        if group_by not in VALID_DIMENSIONS:
            return {"error": f"Unknown dimension '{group_by}'."}
        measure_col = f"SUM(fs.{measure})" if measure != "profit_margin" else "AVG(fs.profit_margin)"
        where = _where(filters or {})
        order = "ASC" if ascending else "DESC"

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
        df = get_db().execute(sql).df()
        df["rank"] = range(1, len(df) + 1)
        return {
            "operation": "top_n",
            "measure": measure,
            "n": n,
            "group_by": group_by,
            "ascending": ascending,
            "columns": ["rank", "group_dim", "metric", "order_count"],
            "rows": df[["rank", "group_dim", "metric", "order_count"]].round(2).to_dict(orient="records"),
            "row_count": len(df),
        }

    def compare_periods(
        self,
        period_a: dict[str, Any],
        period_b: dict[str, Any],
        measure: str = "revenue",
        group_by: str | None = None,
    ) -> dict[str, Any]:
        """
        Compare two arbitrary time periods (e.g. Q3 vs Q4, 2023 vs 2024).

        period_a / period_b are filter dicts, e.g. {'year': 2024, 'quarter': 3}
        """
        def _fetch(filters: dict) -> pd.DataFrame:
            where = _where(filters)
            measure_col = f"SUM(fs.{measure})" if measure != "profit_margin" else "AVG(fs.profit_margin)"
            dim_select = f", {_col(group_by)} AS group_dim" if group_by else ""
            dim_group = f", {_col(group_by)}" if group_by else ""
            sql = f"""
            SELECT {measure_col} AS metric {dim_select}
            {BASE_JOIN}
            {where}
            GROUP BY 1=1 {dim_group}
            """
            return get_db().execute(sql).df()

        df_a = _fetch(period_a)
        df_b = _fetch(period_b)

        if group_by:
            merged = df_a.merge(df_b, on="group_dim", suffixes=("_a", "_b"), how="outer").fillna(0)
            merged["abs_change"] = (merged["metric_b"] - merged["metric_a"]).round(2)
            merged["pct_change"] = (
                (merged["metric_b"] - merged["metric_a"]) / merged["metric_a"].replace(0, float("nan")) * 100
            ).round(2)
            rows = merged.round(2).to_dict(orient="records")
        else:
            val_a = df_a["metric"].iloc[0] if len(df_a) else 0
            val_b = df_b["metric"].iloc[0] if len(df_b) else 0
            abs_change = round(val_b - val_a, 2)
            pct_change = round((abs_change / val_a * 100), 2) if val_a else None
            rows = [{
                "period_a": period_a, "period_b": period_b,
                "value_a": round(val_a, 2), "value_b": round(val_b, 2),
                "abs_change": abs_change, "pct_change": pct_change,
            }]

        return {
            "operation": "compare_periods",
            "measure": measure,
            "period_a": period_a,
            "period_b": period_b,
            "group_by": group_by,
            "rows": rows,
        }

    def revenue_share(
        self,
        group_by: str = "region",
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return each group's percentage share of total revenue."""
        if group_by not in VALID_DIMENSIONS:
            return {"error": f"Unknown dimension '{group_by}'."}
        where = _where(filters or {})

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
        df = get_db().execute(sql).df()
        return {
            "operation": "revenue_share",
            "group_by": group_by,
            "columns": list(df.columns),
            "rows": df.round(2).to_dict(orient="records"),
        }
