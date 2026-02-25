"""
Cube Operations Agent
──────────────────────
Handles OLAP cube manipulations:
  • Slice  – filter on a single dimension value
  • Dice   – filter on multiple dimension values
  • Pivot  – reorganise data across two dimensions
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
    "month_name": "dd.month_name",
    "region": "dg.region",
    "country": "dg.country",
    "category": "dp.category",
    "subcategory": "dp.subcategory",
    "customer_segment": "dc.customer_segment",
}

VALID_MEASURES = {"revenue", "profit", "cost", "quantity", "profit_margin"}


def _col(dim: str) -> str:
    return VALID_DIMENSIONS.get(dim, dim)


def _where(filters: dict[str, Any]) -> str:
    clauses: list[str] = []
    for k, v in filters.items():
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


def _measure_expr(measure: str) -> str:
    if measure == "profit_margin":
        return "AVG(fs.profit_margin)"
    return f"SUM(fs.{measure})"


class CubeOperationsAgent:
    """Performs OLAP cube slice, dice, and pivot operations."""

    def slice(
        self,
        dimension: str,
        value: Any,
        group_by: list[str] | None = None,
        measures: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Slice the cube by fixing one dimension to a single value.

        Example: slice(dimension='year', value=2024)
        """
        if dimension not in VALID_DIMENSIONS:
            return {"error": f"Unknown dimension '{dimension}'. Valid: {list(VALID_DIMENSIONS)}"}

        measures = [m for m in (measures or ["revenue", "profit"]) if m in VALID_MEASURES]
        # Default to grouping by the slice dimension if no group_by provided
        group_by = [g for g in (group_by or [dimension]) if g in VALID_DIMENSIONS]

        select_parts = []
        if group_by:
            select_parts.append(", ".join(_col(g) + f" AS {g}" for g in group_by))
        
        select_parts.append(", ".join(f"{_measure_expr(m)} AS total_{m}" for m in measures))
        select_dims_measures = ", ".join(p for p in select_parts if p)
        
        group_clause = ""
        if group_by:
            group_clause = "GROUP BY " + ", ".join(_col(g) for g in group_by)
            order_clause = "ORDER BY " + ", ".join(_col(g) for g in group_by)
        else:
            order_clause = ""

        where = _where({dimension: value})

        sql = f"""
        SELECT {select_dims_measures},
               COUNT(*) AS order_count
        {BASE_JOIN}
        {where}
        {group_clause}
        {order_clause}
        """

        df = get_db().execute(sql).df()
        return {
            "operation": "slice",
            "dimension": dimension,
            "value": value,
            "group_by": group_by,
            "measures": measures,
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "row_count": len(df),
        }

    def dice(
        self,
        filters: dict[str, Any],
        group_by: list[str] | None = None,
        measures: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Dice the cube by applying multiple dimension filters simultaneously.

        Example: dice(filters={'year': 2024, 'region': 'Europe'})
        """
        invalid = [k for k in filters if k not in VALID_DIMENSIONS]
        if invalid:
            return {"error": f"Unknown filter dimensions: {invalid}. Valid: {list(VALID_DIMENSIONS)}"}

        measures = [m for m in (measures or ["revenue", "profit"]) if m in VALID_MEASURES]
        group_by = group_by or list(filters.keys())
        group_by = [g for g in group_by if g in VALID_DIMENSIONS]

        select_parts = []
        if group_by:
            select_parts.append(", ".join(_col(g) + f" AS {g}" for g in group_by))
        
        select_parts.append(", ".join(f"{_measure_expr(m)} AS total_{m}" for m in measures))
        select_dims_measures = ", ".join(p for p in select_parts if p)
        
        group_clause = ""
        if group_by:
            group_clause = "GROUP BY " + ", ".join(_col(g) for g in group_by)
            order_clause = "ORDER BY " + ", ".join(_col(g) for g in group_by)
        else:
            order_clause = ""

        where = _where(filters)

        sql = f"""
        SELECT {select_dims_measures},
               COUNT(*) AS order_count
        {BASE_JOIN}
        {where}
        {group_clause}
        {order_clause}
        """

        df = get_db().execute(sql).df()
        return {
            "operation": "dice",
            "filters": filters,
            "group_by": group_by,
            "measures": measures,
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "row_count": len(df),
        }

    def pivot(
        self,
        rows: str,
        columns: str,
        values: str = "revenue",
        filters: dict[str, Any] | None = None,
        top_n: int | None = None,
    ) -> dict[str, Any]:
        """
        Pivot the cube: rows × columns with aggregated measure values.

        Example: pivot(rows='region', columns='year', values='revenue')
        """
        for dim in [rows, columns]:
            if dim not in VALID_DIMENSIONS:
                return {"error": f"Unknown dimension '{dim}'. Valid: {list(VALID_DIMENSIONS)}"}
        if values not in VALID_MEASURES:
            return {"error": f"Unknown measure '{values}'. Valid: {list(VALID_MEASURES)}"}

        where = _where(filters or {})
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

        df = get_db().execute(sql).df()
        pivoted = df.pivot_table(index="row_dim", columns="col_dim", values="val", aggfunc="sum")
        pivoted = pivoted.reset_index()
        pivoted.columns.name = None
        pivoted.columns = [str(c) for c in pivoted.columns]

        if top_n:
            total_col = f"total_{values}"
            pivoted[total_col] = pivoted.iloc[:, 1:].sum(axis=1)
            pivoted = pivoted.nlargest(top_n, total_col).drop(columns=[total_col])

        return {
            "operation": "pivot",
            "rows": rows,
            "columns": columns,
            "values": values,
            "filters": filters or {},
            "columns_list": list(pivoted.columns),
            "rows_list": pivoted.to_dict(orient="records"),
            "row_count": len(pivoted),
        }

    def get_dimension_values(self, dimension: str) -> dict[str, Any]:
        """Return all distinct values for a given dimension."""
        if dimension not in VALID_DIMENSIONS:
            return {"error": f"Unknown dimension '{dimension}'."}

        col = _col(dimension)
        sql = f"""
        SELECT DISTINCT {col} AS value
        {BASE_JOIN}
        ORDER BY {col}
        """
        rows = get_db().execute(sql).fetchall()
        return {"dimension": dimension, "values": [r[0] for r in rows]}
