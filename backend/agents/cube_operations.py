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

from database.repository import SalesRepository, VALID_DIMENSIONS, VALID_MEASURES, _where as _repo_where

_repo = SalesRepository()


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

        df = _repo.get_slice(dimension, value, group_by, measures)
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

        df = _repo.get_dice(filters, group_by, measures)
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

        df = _repo.get_pivot_data(rows, columns, values, filters or {})
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

        values = _repo.get_dimension_values(dimension)
        return {"dimension": dimension, "values": values}
