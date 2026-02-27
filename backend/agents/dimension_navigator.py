"""
Dimension Navigator Agent
─────────────────────────
Handles hierarchical OLAP operations:
  • Drill-Down : coarser level → finer level  (Year → Quarter → Month)
  • Roll-Up    : finer level  → coarser level (Month → Quarter → Year)

Supported hierarchies
  Time      : year → quarter → month
  Geography : region → country
  Product   : category → subcategory
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from database.repository import SalesRepository
from database.repository import _where as _repo_where

# ── Hierarchy definitions ─────────────────────────────────────────────────────
HIERARCHIES: dict[str, dict] = {
    "time": {
        "levels": ["year", "quarter", "month"],
        "tables": {
            "year": "dd.year",
            "quarter": "dd.year, dd.quarter",
            "month": "dd.year, dd.quarter, dd.month, dd.month_name",
        },
        "labels": {
            "year": ["year"],
            "quarter": ["year", "quarter"],
            "month": ["year", "quarter", "month", "month_name"],
        },
    },
    "geography": {
        "levels": ["region", "country"],
        "tables": {
            "region": "dg.region",
            "country": "dg.region, dg.country",
        },
        "labels": {
            "region": ["region"],
            "country": ["region", "country"],
        },
    },
    "product": {
        "levels": ["category", "subcategory"],
        "tables": {
            "category": "dp.category",
            "subcategory": "dp.category, dp.subcategory",
        },
        "labels": {
            "category": ["category"],
            "subcategory": ["category", "subcategory"],
        },
    },
}


_repo = SalesRepository()


class DimensionNavigatorAgent:
    """
    Navigates OLAP hierarchies (drill-down and roll-up).
    """

    def drill_down(
        self,
        hierarchy: str,
        from_level: str,
        to_level: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Drill down from *from_level* to the next finer level (or *to_level*).

        Returns aggregated revenue/profit grouped at the new level.
        """
        h = HIERARCHIES.get(hierarchy)
        if h is None:
            return {
                "error": f"Unknown hierarchy '{hierarchy}'. Choose from: {list(HIERARCHIES)}"
            }

        levels = h["levels"]
        if from_level not in levels:
            return {
                "error": f"'{from_level}' not in {hierarchy} hierarchy levels: {levels}"
            }

        from_idx = levels.index(from_level)
        if to_level is None:
            if from_idx == len(levels) - 1:
                return {"error": f"Already at the finest level '{from_level}'."}
            to_level = levels[from_idx + 1]
        elif to_level not in levels or levels.index(to_level) <= from_idx:
            return {"error": f"'{to_level}' is not finer than '{from_level}'."}

        group_cols = h["tables"][to_level]
        label_cols = h["labels"][to_level]
        where_clause, params = _repo_where(filters or {})
        df = _repo.get_hierarchy_data(group_cols, where_clause, group_cols, params)
        return {
            "operation": "drill_down",
            "hierarchy": hierarchy,
            "from_level": from_level,
            "to_level": to_level,
            "filters": filters or {},
            "group_by": label_cols,
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "row_count": len(df),
        }

    def roll_up(
        self,
        hierarchy: str,
        from_level: str,
        to_level: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Roll up from *from_level* to the next coarser level (or *to_level*).
        """
        h = HIERARCHIES.get(hierarchy)
        if h is None:
            return {
                "error": f"Unknown hierarchy '{hierarchy}'. Choose from: {list(HIERARCHIES)}"
            }

        levels = h["levels"]
        if from_level not in levels:
            return {
                "error": f"'{from_level}' not in {hierarchy} hierarchy levels: {levels}"
            }

        from_idx = levels.index(from_level)
        if to_level is None:
            if from_idx == 0:
                return {"error": f"Already at the coarsest level '{from_level}'."}
            to_level = levels[from_idx - 1]
        elif to_level not in levels or levels.index(to_level) >= from_idx:
            return {"error": f"'{to_level}' is not coarser than '{from_level}'."}

        group_cols = h["tables"][to_level]
        label_cols = h["labels"][to_level]
        where_clause, params = _repo_where(filters or {})
        df = _repo.get_hierarchy_data(group_cols, where_clause, group_cols, params)
        return {
            "operation": "roll_up",
            "hierarchy": hierarchy,
            "from_level": from_level,
            "to_level": to_level,
            "filters": filters or {},
            "group_by": label_cols,
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "row_count": len(df),
        }

    def get_hierarchy_info(self) -> dict[str, Any]:
        """Return available hierarchies and their level structures."""
        return {name: {"levels": h["levels"]} for name, h in HIERARCHIES.items()}

    def drill_through(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Drill through to raw fact table records (detail transactions).

        This operation returns the underlying individual sales transactions
        instead of aggregated data. This allows users to see the actual
        detailed records that make up any aggregated metric.

        Parameters
        ----------
        filters : dict
            Optional filters to apply (e.g. {"year": 2024, "region": "Europe"})
        limit : int
            Maximum number of records to return (default: 100, max: 1000)

        Returns
        -------
        dict
            Operation result with individual fact_sales records including
            all dimensions and measures.

        Example
        -------
        drill_through(filters={"year": 2024, "category": "Electronics"}, limit=50)
        """
        if limit > 1000:
            limit = 1000

        where_clause, params = _repo_where(filters or {})

        sql = f"""
        SELECT
            fs.order_id,
            dd.year,
            dd.quarter,
            dd.month,
            dd.month_name,
            dg.region,
            dg.country,
            dp.category,
            dp.subcategory,
            dc.customer_segment,
            fs.quantity,
            fs.unit_price,
            fs.revenue,
            fs.cost,
            fs.profit,
            fs.profit_margin
        FROM fact_sales fs
        JOIN dim_date      dd ON fs.date_id     = dd.date_id
        JOIN dim_geography dg ON fs.geo_id      = dg.geo_id
        JOIN dim_product   dp ON fs.product_id  = dp.product_id
        JOIN dim_customer  dc ON fs.customer_id = dc.customer_id
        {where_clause}
        ORDER BY dd.year DESC, dd.month DESC, fs.revenue DESC
        LIMIT ?
        """

        params.append(limit)
        df = _repo._execute(sql, params)

        return {
            "operation": "drill_through",
            "filters": filters or {},
            "limit": limit,
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "row_count": len(df),
        }
