"""
Visualization Agent
────────────────────
Rule-based chart-type selector.  Inspects the result data structure and
operation type to return a Recharts-compatible chart_config dict.

Chart selection rules
─────────────────────
  time series (year / month columns)     → LineChart
  part-of-whole  (revenue_share)         → PieChart
  multi-measure comparisons              → ComposedChart
  categorical ranking / single measure  → BarChart (default)
"""

from __future__ import annotations

from typing import Any

COLORS = ["#2E75B6", "#00B0F0", "#1F7A4D", "#C55A11", "#5B2D8E", "#C00000"]


class VisualizationAgent:
    """
    Determines the best chart type for a given OLAP result and returns
    a Recharts-compatible configuration object.
    """

    def recommend(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Return a chart_config dict for the given agent result.

        Parameters
        ----------
        data : raw result dict from any specialist agent
        """
        operation = data.get("operation", "")
        if operation == "pivot":
            rows = data.get("rows_list", [])
        else:
            rows = data.get("rows", data.get("rows_list", []))

        if not rows or not isinstance(rows, list):
            return {}
        cols = list(rows[0].keys()) if rows else []

        # Detect axis candidates
        x_axis = self._pick_x_axis(cols, operation)
        numeric_cols = [
            c for c in cols
            if c != x_axis and self._is_numeric(rows, c)
        ]

        chart_type, y_axes = self._pick_chart(operation, cols, numeric_cols)

        title = self._title(operation, data)

        return {
            "chart_type": chart_type,
            "x_axis": x_axis,
            "y_axes": y_axes,
            "title": title,
            "show_legend": len(y_axes) > 1,
            "show_grid": True,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _pick_x_axis(self, cols: list[str], operation: str) -> str:
        """Choose the most appropriate x-axis field."""
        time_cols = ["month_name", "month", "quarter", "year"]
        for tc in time_cols:
            if tc in cols:
                return tc
        for candidate in ["group_dim", "region", "country", "category",
                          "subcategory", "customer_segment", "row_dim"]:
            if candidate in cols:
                return candidate
        return cols[0] if cols else "label"

    def _is_numeric(self, rows: list[dict], col: str) -> bool:
        """Return True if the column contains predominantly numeric values."""
        sample = [r.get(col) for r in rows[:5] if r.get(col) is not None]
        return bool(sample) and all(isinstance(v, (int, float)) for v in sample)

    def _pick_chart(
        self,
        operation: str,
        all_cols: list[str],
        numeric_cols: list[str],
    ) -> tuple[str, list[dict]]:
        """Return (chart_type, y_axes list)."""
        # Time-series operations → Line
        if operation in ("yoy_growth", "mom_change", "ytd_revenue", "rolling_avg") or any(
            c in all_cols for c in ("month", "month_name", "quarter")
        ):
            measure_cols = [c for c in numeric_cols
                            if c in ("metric", "current", "total_revenue", "monthly_value",
                                     "abs_change", "pct_change") or
                               c.startswith("ytd_") or c.startswith("rolling_") or c.startswith("monthly_")]
            if not measure_cols:
                measure_cols = numeric_cols[:3]
            y_axes = [
                {"field": c, "color": COLORS[i % len(COLORS)], "type": "line", "label": c.replace("_", " ").title()}
                for i, c in enumerate(measure_cols)
            ]
            return "LineChart", y_axes

        # Part-of-whole → Pie
        if operation == "revenue_share" or "share_pct" in " ".join(all_cols):
            value_col = next(
                (c for c in numeric_cols if "share" in c or "pct" in c),
                numeric_cols[0] if numeric_cols else "value",
            )
            return "PieChart", [
                {"field": value_col, "color": COLORS[0], "type": "pie", "label": value_col}
            ]

        # Multi-measure (compare_periods with group_by) → ComposedChart
        if operation == "compare_periods" and len(numeric_cols) >= 2:
            y_axes = [
                {"field": c, "color": COLORS[i % len(COLORS)], "type": "bar", "label": c}
                for i, c in enumerate(numeric_cols[:3])
            ]
            return "ComposedChart", y_axes

        # Default: BarChart with primary measure
        primary = next(
            (c for c in numeric_cols
             if c in ("metric", "total_revenue", "avg_margin", "group_revenue")),
            numeric_cols[0] if numeric_cols else "value",
        )
        y_axes = [{"field": primary, "color": COLORS[0], "type": "bar", "label": primary}]

        # Add secondary line for pct_change if present
        if "pct_change" in numeric_cols:
            y_axes.append({
                "field": "pct_change",
                "color": COLORS[2],
                "type": "line",
                "label": "% Change",
            })
            return "ComposedChart", y_axes

        return "BarChart", y_axes

    def _title(self, operation: str, data: dict) -> str:
        label_map = {
            "slice": "Slice Analysis",
            "dice": "Multi-Dimension Filter",
            "pivot": f"Pivot: {data.get('rows','')} × {data.get('columns','')}",
            "drill_down": f"Drill-Down to {data.get('to_level', '')}",
            "roll_up": f"Roll-Up to {data.get('to_level', '')}",
            "yoy_growth": "Year-over-Year Growth",
            "mom_change": "Monthly Trend",
            "profit_margins": "Profit Margin by Segment",
            "top_n": f"Top {data.get('n', '')} by {data.get('measure', '')}",
            "compare_periods": "Period Comparison",
            "revenue_share": "Revenue Share",
            "drill_through": "Transaction Detail",
            "ytd_revenue": f"YTD {data.get('measure', 'Revenue').title()} — {data.get('year', '')}",
            "rolling_avg": f"Rolling {data.get('window', 3)}-Month Average",
        }
        return label_map.get(operation, operation.replace("_", " ").title())

    def run(self, query: str, params: dict) -> dict[str, Any]:
        """Agent interface used by orchestrator/planner.py."""
        data = params.get("data")
        if isinstance(data, list) and data:
            # Wrap list-of-rows into the expected dict shape
            data_dict = {"operation": params.get("operation", ""), "rows": data}
        elif isinstance(data, dict):
            data_dict = data
        else:
            return {"chart_config": None}
        return {"chart_config": self.recommend(data_dict)}
