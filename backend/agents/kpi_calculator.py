"""KPI Calculator Agent - Uses SalesRepository for all database access."""

from __future__ import annotations
from typing import Any
import pandas as pd
from database.repository import SalesRepository, VALID_DIMENSIONS

_repo = SalesRepository()


class KPICalculatorAgent:
    """Calculates business KPIs from the star-schema data warehouse."""

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
