"""KPI Calculator Agent - Uses SalesRepository for all database access."""

from __future__ import annotations
from typing import Any
import pandas as pd
from database.repository import SalesRepository, VALID_DIMENSIONS

_repo = SalesRepository()


class KPICalculatorAgent:
    """Calculates business KPIs from the star-schema data warehouse."""

    def aggregate(
        self,
        measures: list[str] | None = None,
        functions: list[str] | None = None,
        group_by: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Flexible aggregation: SUM, AVG, COUNT across any dimension with optional filters.
        Handles 'how many orders/transactions', 'total revenue by quarter', etc.
        """
        from database.repository import _where, BASE_JOIN, _col, _measure_expr, VALID_MEASURES
        from database.connection import get_db

        filters = filters or {}
        funcs = functions or ["SUM"]
        measure_list = measures or ["revenue"]

        # Build SELECT parts
        select_parts = []
        if group_by and group_by in VALID_DIMENSIONS:
            select_parts.append(f"{_col(group_by)} AS group_dim")

        for func in funcs:
            func = func.upper()
            if func == "COUNT":
                select_parts.append("COUNT(*) AS order_count")
            elif func == "SUM":
                for m in measure_list:
                    if m in VALID_MEASURES:
                        select_parts.append(f"SUM(fs.{m}) AS total_{m}")
            elif func == "AVG":
                for m in measure_list:
                    if m in VALID_MEASURES:
                        expr = "AVG(fs.profit_margin)" if m == "profit_margin" else f"AVG(fs.{m})"
                        select_parts.append(f"{expr} AS avg_{m}")

        # Always include order count for informational purposes
        if "COUNT(*) AS order_count" not in select_parts:
            select_parts.append("COUNT(*) AS order_count")

        if not select_parts:
            select_parts = ["COUNT(*) AS order_count", "SUM(fs.revenue) AS total_revenue"]

        where, params = _where(filters)
        group_clause = f"GROUP BY {_col(group_by)}" if group_by and group_by in VALID_DIMENSIONS else ""
        order_clause = f"ORDER BY {_col(group_by)}" if group_by and group_by in VALID_DIMENSIONS else ""

        sql = f"""
        SELECT {", ".join(select_parts)}
        {BASE_JOIN}
        {where}
        {group_clause}
        {order_clause}
        """
        df = get_db().execute(sql, params).df()
        return {
            "operation": "aggregate",
            "measures": measure_list,
            "functions": funcs,
            "group_by": group_by,
            "filters": filters,
            "columns": list(df.columns),
            "rows": df.round(2).to_dict(orient="records"),
            "row_count": len(df),
        }

    def yoy_growth(
        self,
        measure: str = "revenue",
        group_by: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """YoY growth for a measure, optionally broken down by a dimension."""
        if measure not in ("revenue", "profit", "cost", "quantity", "profit_margin"):
            return {"error": f"Invalid measure"}
        if group_by and group_by not in VALID_DIMENSIONS:
            return {"error": f"Invalid group_by"}
        df = _repo.get_yoy_data(measure, group_by, filters or {})
        if group_by:
            result_rows = []
            for group_val, grp in df.groupby("group_dim"):
                grp = grp.sort_values("year")
                grp["prev_metric"] = grp["metric"].shift(1)
                grp["abs_change"] = grp["metric"] - grp["prev_metric"]
                grp["pct_change"] = (grp["abs_change"] / grp["prev_metric"] * 100).round(2)
                for _, row in grp.iterrows():
                    result_rows.append({
                        "group": group_val, "year": int(row["year"]),
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
                    "year": int(row["year"]), "current": round(row["metric"], 2),
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
        df = _repo.get_mom_data(measure, year, filters or {})
        df["prev_metric"] = df["metric"].shift(1)
        df["abs_change"] = df["metric"] - df["prev_metric"]
        df["pct_change"] = (df["abs_change"] / df["prev_metric"] * 100).round(2)
        rows = []
        for _, row in df.iterrows():
            rows.append({
                "year": int(row["year"]), "month": int(row["month"]),
                "month_name": row["month_name"], "current": round(row["metric"], 2),
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
            return {"error": f"Unknown dimension"}
        df = _repo.get_profit_margins(group_by, filters or {}, sort_desc)
        return {
            "operation": "profit_margins", "group_by": group_by,
            "columns": list(df.columns), "rows": df.round(2).to_dict(orient="records"),
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
            return {"error": f"Unknown dimension"}
        df = _repo.get_top_n(measure, n, group_by, filters or {}, ascending)
        df["rank"] = range(1, len(df) + 1)
        return {
            "operation": "top_n", "measure": measure, "n": n,
            "group_by": group_by, "ascending": ascending,
            "columns": ["rank", "group_dim", "metric", "order_count"],
            "rows": df[["rank", "group_dim", "metric", "order_count"]].round(2).to_dict(orient="records"),
            "row_count": len(df),
        }

    def compare_periods(
        self,
        period_a: dict[str, Any] = None,
        period_b: dict[str, Any] = None,
        measure: str = "revenue",
        group_by: str | None = None,
    ) -> dict[str, Any]:
        """Compare two arbitrary time periods."""
        df_a = _repo.get_period_data(period_a, measure, group_by)
        df_b = _repo.get_period_data(period_b, measure, group_by)
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
            rows = [{"period_a": period_a, "period_b": period_b,
                     "value_a": round(val_a, 2), "value_b": round(val_b, 2),
                     "abs_change": abs_change, "pct_change": pct_change}]
        return {"operation": "compare_periods", "measure": measure,
                "period_a": period_a, "period_b": period_b, "group_by": group_by, "rows": rows}

    def revenue_share(
        self,
        group_by: str = "region",
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return each group percentage share of total revenue."""
        if group_by not in VALID_DIMENSIONS:
            return {"error": f"Unknown dimension"}
        df = _repo.get_revenue_share(group_by, filters or {})
        return {
            "operation": "revenue_share", "group_by": group_by,
            "columns": list(df.columns), "rows": df.round(2).to_dict(orient="records"),
        }

    def ytd_revenue(
        self,
        year: int = 2024,
        measure: str = "revenue",
        group_by: str | None = None,
    ) -> dict[str, Any]:
        """Year-to-date cumulative revenue for a given year, optionally by dimension."""
        from database.repository import _where, BASE_JOIN, _col, _measure_expr
        from database.connection import get_db
        measure_col = _measure_expr(measure)
        dim_select = f", {_col(group_by)} AS group_dim" if group_by else ""
        dim_group = f", {_col(group_by)}" if group_by else ""
        # Use a subquery to avoid mixing window functions with GROUP BY aggregates
        sql = f"""
        WITH monthly AS (
            SELECT dd.month, dd.month_name {dim_select},
                   {measure_col} AS monthly_{measure}
            {BASE_JOIN}
            WHERE dd.year = ?
            GROUP BY dd.month, dd.month_name {dim_group}
        )
        SELECT *,
               SUM(monthly_{measure}) OVER (
                   {"PARTITION BY group_dim " if group_by else ""}ORDER BY month
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
               ) AS ytd_{measure}
        FROM monthly
        ORDER BY month {", group_dim" if group_by else ""}
        """
        df = get_db().execute(sql, [year]).df()
        return {
            "operation": "ytd_revenue",
            "measure": measure,
            "year": year,
            "group_by": group_by,
            "columns": list(df.columns),
            "rows": df.round(2).to_dict(orient="records"),
        }

    def rolling_avg(
        self,
        measure: str = "revenue",
        window: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Rolling N-month average for a measure (time intelligence)."""
        from database.repository import _where, BASE_JOIN, _measure_expr
        from database.connection import get_db
        measure_col = _measure_expr(measure)
        where, params = _where(filters or {})
        # Use subquery to avoid mixing window functions with GROUP BY aggregates
        sql = f"""
        WITH monthly AS (
            SELECT dd.year, dd.month, dd.month_name,
                   {measure_col} AS monthly_value
            {BASE_JOIN}
            {where}
            GROUP BY dd.year, dd.month, dd.month_name
        )
        SELECT *,
               AVG(monthly_value) OVER (
                   ORDER BY year, month
                   ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW
               ) AS rolling_{window}m_avg
        FROM monthly
        ORDER BY year, month
        """
        df = get_db().execute(sql, params).df()
        return {
            "operation": "rolling_avg",
            "measure": measure,
            "window": window,
            "columns": list(df.columns),
            "rows": df.round(2).to_dict(orient="records"),
        }
