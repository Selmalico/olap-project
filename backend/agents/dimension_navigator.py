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

from database.connection import get_db

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

BASE_JOIN = """
FROM fact_sales fs
JOIN dim_date     dd ON fs.date_id     = dd.date_id
JOIN dim_geography dg ON fs.geo_id     = dg.geo_id
JOIN dim_product   dp ON fs.product_id = dp.product_id
JOIN dim_customer  dc ON fs.customer_id= dc.customer_id
"""


def _build_where(filters: dict[str, Any]) -> str:
    """Convert a filter dict into a SQL WHERE clause."""
    clauses: list[str] = []
    mapping = {
        "year": "dd.year",
        "quarter": "dd.quarter",
        "month": "dd.month",
        "month_name": "dd.month_name",
        "region": "dg.region",
        "country": "dg.country",
        "category": "dp.category",
        "subcategory": "dp.subcategory",
        "customer_segment": "dc.customer_segment",
    }
    for key, value in (filters or {}).items():
        col = mapping.get(key)
        if not col:
            continue
        if isinstance(value, list):
            quoted = ", ".join(f"'{v}'" for v in value)
            clauses.append(f"{col} IN ({quoted})")
        elif isinstance(value, (int, float)):
            clauses.append(f"{col} = {value}")
        else:
            clauses.append(f"{col} = '{value}'")
    return ("WHERE " + " AND ".join(clauses)) if clauses else ""


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
            return {"error": f"Unknown hierarchy '{hierarchy}'. Choose from: {list(HIERARCHIES)}"}

        levels = h["levels"]
        if from_level not in levels:
            return {"error": f"'{from_level}' not in {hierarchy} hierarchy levels: {levels}"}

        from_idx = levels.index(from_level)
        if to_level is None:
            if from_idx == len(levels) - 1:
                return {"error": f"Already at the finest level '{from_level}'."}
            to_level = levels[from_idx + 1]
        elif to_level not in levels or levels.index(to_level) <= from_idx:
            return {"error": f"'{to_level}' is not finer than '{from_level}'."}

        group_cols = h["tables"][to_level]
        label_cols = h["labels"][to_level]
        where_clause = _build_where(filters or {})

        sql = f"""
        SELECT {group_cols},
               SUM(fs.revenue)  AS total_revenue,
               SUM(fs.profit)   AS total_profit,
               SUM(fs.quantity) AS total_quantity,
               COUNT(*)         AS order_count,
               AVG(fs.profit_margin) AS avg_margin
        {BASE_JOIN}
        {where_clause}
        GROUP BY {group_cols}
        ORDER BY {group_cols}
        """

        df = get_db().execute(sql).df()
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
            return {"error": f"Unknown hierarchy '{hierarchy}'. Choose from: {list(HIERARCHIES)}"}

        levels = h["levels"]
        if from_level not in levels:
            return {"error": f"'{from_level}' not in {hierarchy} hierarchy levels: {levels}"}

        from_idx = levels.index(from_level)
        if to_level is None:
            if from_idx == 0:
                return {"error": f"Already at the coarsest level '{from_level}'."}
            to_level = levels[from_idx - 1]
        elif to_level not in levels or levels.index(to_level) >= from_idx:
            return {"error": f"'{to_level}' is not coarser than '{from_level}'."}

        group_cols = h["tables"][to_level]
        label_cols = h["labels"][to_level]
        where_clause = _build_where(filters or {})

        sql = f"""
        SELECT {group_cols},
               SUM(fs.revenue)  AS total_revenue,
               SUM(fs.profit)   AS total_profit,
               SUM(fs.quantity) AS total_quantity,
               COUNT(*)         AS order_count,
               AVG(fs.profit_margin) AS avg_margin
        {BASE_JOIN}
        {where_clause}
        GROUP BY {group_cols}
        ORDER BY {group_cols}
        """

        df = get_db().execute(sql).df()
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
        return {
            name: {"levels": h["levels"]}
            for name, h in HIERARCHIES.items()
        }
