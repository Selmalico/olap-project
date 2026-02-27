"""
Report Generator Agent
───────────────────────
Formats raw agent results into presentable reports:
  • Formatted tables with totals row
  • Conditional formatting hints (colour thresholds)
  • Executive summary text (enhanced by Hugging Face)
  • Dashboard summary cards
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger("selma")


def _to_float(v):
    """Convert to native float (handles numpy, None, nan)."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if (f != f) else f  # nan != nan
    except (TypeError, ValueError):
        return None


def _pct_fmt(v: float | None) -> str:
    f = _to_float(v)
    if f is None:
        return "—"
    sign = "+" if f > 0 else ""
    return f"{sign}{f:.1f}%"


def _money_fmt(v: float | None) -> str:
    f = _to_float(v)
    if f is None:
        return "—"
    return f"${f:,.2f}"


def _colour_hint(v: float | None) -> str:
    """Return a simple colour keyword based on value."""
    if v is None:
        return "neutral"
    if v > 5:
        return "green"
    if v < -5:
        return "red"
    return "yellow"


class ReportGeneratorAgent:
    """Formats agent results into structured, UI-ready reports."""

    def __init__(self) -> None:
        self._hf_client = None
        self._model = "Qwen/Qwen2.5-7B-Instruct"
        
        hf_token = (os.getenv("HUGGINGFACE_TOKEN") or "").strip()

        if hf_token:
            try:
                from huggingface_hub import InferenceClient
                self._hf_client = InferenceClient(model=self._model, token=hf_token)
                logger.info(f"ReportGenerator: Hugging Face enabled ({self._model})")
            except Exception as e:
                logger.warning("ReportGenerator: Hugging Face initialization failed: %s", e)

    def generate_table(
        self,
        data: dict[str, Any],
        title: str | None = None,
        add_totals: bool = True,
        format_money: list[str] | None = None,
        format_pct: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Transform raw agent output into a formatted table report.

        Parameters
        ----------
        data         : raw result dict from any agent
        title        : optional report title override
        add_totals   : append a totals row for numeric columns
        format_money : column names to format as currency
        format_pct   : column names to format as percentage
        """
        # Pivot returns "rows"/"columns" as dimension names (str); table data is in rows_list/columns_list
        if data.get("operation") == "pivot":
            rows = data.get("rows_list", [])
            columns = data.get("columns_list", [])
        else:
            rows = data.get("rows", data.get("rows_list", []))
            columns = data.get("columns", data.get("columns_list", list(rows[0].keys()) if rows and isinstance(rows, list) else []))

        if not rows:
            return {"title": title or "Empty Report", "table": [], "columns": [], "summary": "No data found."}

        df = pd.DataFrame(rows)
        money_cols = set(format_money or [c for c in df.columns if "revenue" in c or "profit" in c or "cost" in c or "metric" in c])
        pct_cols = set(format_pct or [c for c in df.columns if "pct" in c or "margin" in c or "share" in c])

        formatted_rows = []
        for _, row in df.iterrows():
            frow = {}
            for col in df.columns:
                val = row[col]
                if col in money_cols and isinstance(val, (int, float)) and not pd.isna(val):
                    frow[col] = _money_fmt(val)
                elif col in pct_cols and isinstance(val, (int, float)) and not pd.isna(val):
                    frow[col] = _pct_fmt(val)
                else:
                    if pd.isna(val) or (isinstance(val, float) and val != val):
                        frow[col] = None
                    elif hasattr(val, "item"):
                        frow[col] = val.item()
                    else:
                        frow[col] = val
            formatted_rows.append(frow)

        totals_row = None
        if add_totals:
            totals: dict[str, Any] = {"_totals": True}
            for col in df.columns:
                if col in money_cols and pd.api.types.is_numeric_dtype(df[col]):
                    totals[col] = _money_fmt(df[col].sum())
                elif col in pct_cols and pd.api.types.is_numeric_dtype(df[col]):
                    totals[col] = _pct_fmt(df[col].mean())
                elif pd.api.types.is_numeric_dtype(df[col]):
                    totals[col] = round(df[col].sum(), 2)
                else:
                    totals[col] = "TOTAL"
            totals_row = totals

        # Conditional formatting hints for pct_change columns
        hints = []
        for col in df.columns:
            if "pct_change" in col or "pct" in col:
                if pd.api.types.is_numeric_dtype(df[col]):
                    hints.append({
                        "column": col,
                        "thresholds": [
                            {"min": 5, "color": "green"},
                            {"min": -5, "max": 5, "color": "yellow"},
                            {"max": -5, "color": "red"},
                        ],
                    })

        operation = data.get("operation", "query")
        auto_title = title or self._generate_title(data)

        return {
            "title": auto_title,
            "operation": operation,
            "columns": list(df.columns),
            "rows": formatted_rows,
            "totals_row": totals_row,
            "row_count": len(formatted_rows),
            "conditional_formatting": hints,
        }

    def executive_summary(
        self,
        data: dict[str, Any],
        context: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate an executive summary from an agent result using Hugging Face.
        """
        # Heuristic fallback first
        operation = data.get("operation", "unknown")
        if operation == "pivot":
            rows = data.get("rows_list", [])
        else:
            rows = data.get("rows", data.get("rows_list", []))

        if not rows or not isinstance(rows, list):
            return {"summary": "No data available for this query.", "highlights": [], "recommendations": []}

        df = pd.DataFrame(rows)
        highlights: list[str] = []
        recommendations: list[str] = []
        summary_lines: list[str] = []

        summary_lines.append(f"Analysis covers {len(rows)} data point(s).")

        if operation == "yoy_growth":
            measure = data.get("measure", "revenue")
            if "pct_change" not in df.columns:
                summary_lines.append(f"YoY {measure} data (no growth %).")
            else:
                valid = df[df["pct_change"].notna()]
                if len(valid):
                    best = valid.loc[valid["pct_change"].idxmax()]
                    worst = valid.loc[valid["pct_change"].idxmin()]
                    avg_growth = valid["pct_change"].mean()
                    summary_lines.append(f"Average YoY {measure} growth: {_pct_fmt(avg_growth)}.")
                    best_label = best.get("group", best.get("year", ""))
                    if hasattr(best_label, "item"):
                        best_label = best_label.item()
                    highlights.append(f"Best YoY growth: {_pct_fmt(best['pct_change'])} in {best_label}")
                    if _to_float(worst["pct_change"]) is not None and _to_float(worst["pct_change"]) < 0:
                        worst_label = worst.get("group", worst.get("year", ""))
                        if hasattr(worst_label, "item"):
                            worst_label = worst_label.item()
                        highlights.append(f"Decline: {_pct_fmt(worst['pct_change'])} in {worst_label}")
                        recommendations.append("Investigate the declining segment and consider targeted interventions.")

        elif operation in ("slice", "dice"):
            if "total_revenue" in df.columns:
                total = df["total_revenue"].sum()
                top_row = df.loc[df["total_revenue"].idxmax()]
                summary_lines.append(f"Total revenue in scope: {_money_fmt(total)}.")
                group_col = [c for c in df.columns if c not in ("total_revenue", "total_profit", "order_count", "avg_margin")]
                if group_col:
                    highlights.append(f"Top performer: {top_row[group_col[0]]} ({_money_fmt(top_row['total_revenue'])})")

        elif operation == "top_n":
            measure = data.get("measure", "metric")
            ascending = data.get("ascending", False)
            label = "Bottom" if ascending else "Top"
            summary_lines.append(f"{label} {len(rows)} by {measure}.")
            if rows:
                top = rows[0]
                highlights.append(f"#{1}: {top.get('group_dim')} — {_money_fmt(top.get('metric'))}")

        elif operation == "profit_margins":
            if "avg_margin" in df.columns:
                best = df.loc[df["avg_margin"].idxmax()]
                worst = df.loc[df["avg_margin"].idxmin()]
                overall_avg = df["avg_margin"].mean()
                summary_lines.append(f"Overall average margin: {_pct_fmt(overall_avg)}.")
                highlights.append(f"Highest margin: {best['group_dim']} at {_pct_fmt(best['avg_margin'])}")
                highlights.append(f"Lowest margin: {worst['group_dim']} at {_pct_fmt(worst['avg_margin'])}")
                if worst["avg_margin"] < 20:
                    recommendations.append(f"Review pricing strategy for {worst['group_dim']} — margin below 20%.")

        elif operation == "compare_periods":
            if rows and "pct_change" in rows[0]:
                pct = rows[0].get("pct_change")
                summary_lines.append(f"Period-over-period change: {_pct_fmt(pct)}.")
                if pct and pct > 0:
                    highlights.append("Performance improved compared to the prior period.")
                elif pct and pct < 0:
                    highlights.append("Performance declined compared to the prior period.")
                    recommendations.append("Examine contributing factors to the decline and prioritise recovery actions.")

        elif operation in ("drill_down", "roll_up"):
            to_level = data.get("to_level", "level")
            summary_lines.append(f"Drill {'down' if operation == 'drill_down' else 'up'} to {to_level} level.")
            if "total_revenue" in df.columns:
                highlights.append(f"Total revenue: {_money_fmt(df['total_revenue'].sum())}")

        heuristic_summary = {
            "summary": " ".join(summary_lines),
            "highlights": highlights,
            "recommendations": recommendations,
            "operation": operation,
        }

        # Use Hugging Face for a better summary if available
        if self._hf_client:
            try:
                prompt = f"""
                You are a senior Business Intelligence analyst. 
                Generate a concise executive summary based on the following OLAP data result.
                
                Data (JSON): {json.dumps(data, default=str)}
                Heuristic Baseline: {heuristic_summary['summary']}
                
                Return a JSON object with:
                - "summary": A 1-2 sentence overview.
                - "highlights": A list of 2-3 key insights.
                - "recommendations": A list of 1-2 suggested actions.
                """
                
                response = self._hf_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                )
                
                text = response.choices[0].message.content.strip()
                # Simple extraction of JSON if model wraps it in markdown
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                gemini_data = json.loads(text)
                return {
                    "summary": gemini_data.get("summary", heuristic_summary["summary"]),
                    "highlights": gemini_data.get("highlights", heuristic_summary["highlights"]),
                    "recommendations": gemini_data.get("recommendations", heuristic_summary["recommendations"]),
                    "operation": operation,
                    "generated_by": "huggingface"
                }
            except Exception as e:
                logger.warning("Hugging Face summary generation failed: %s", e)
                return heuristic_summary

        return heuristic_summary

    def dashboard_cards(self, db_conn=None) -> list[dict[str, Any]]:
        """
        Return a list of KPI cards for the dashboard overview.
        Queries the DB directly for aggregate totals.
        """
        from database.connection import get_db
        conn = db_conn or get_db()

        sql = """
        SELECT
            SUM(fs.revenue)       AS total_revenue,
            SUM(fs.profit)        AS total_profit,
            AVG(fs.profit_margin) AS avg_margin,
            SUM(fs.quantity)      AS total_quantity,
            COUNT(*)              AS total_orders,
            COUNT(DISTINCT dg.country) AS countries,
            MIN(dd.year)          AS min_year,
            MAX(dd.year)          AS max_year
        FROM fact_sales fs
        JOIN dim_date      dd ON fs.date_id     = dd.date_id
        JOIN dim_geography dg ON fs.geo_id      = dg.geo_id
        """
        row = conn.execute(sql).fetchone()
        total_revenue, total_profit, avg_margin, total_qty, total_orders, countries, min_year, max_year = row

        return [
            {"label": "Total Revenue", "value": _money_fmt(total_revenue), "icon": "dollar", "color": "blue"},
            {"label": "Total Profit", "value": _money_fmt(total_profit), "icon": "trending-up", "color": "green"},
            {"label": "Avg Profit Margin", "value": _pct_fmt(avg_margin), "icon": "percent", "color": "purple"},
            {"label": "Total Orders", "value": f"{total_orders:,}", "icon": "shopping-cart", "color": "orange"},
            {"label": "Units Sold", "value": f"{int(total_qty):,}", "icon": "package", "color": "teal"},
            {"label": "Countries", "value": str(countries), "icon": "globe", "color": "pink"},
        ]

    def _generate_title(self, data: dict[str, Any]) -> str:
        op = data.get("operation", "Query")
        label_map = {
            "slice": "Slice Analysis",
            "dice": "Multi-Dimension Filter",
            "pivot": f"Pivot: {data.get('rows','')} × {data.get('columns','')}",
            "drill_down": f"Drill-Down: {data.get('from_level','')} → {data.get('to_level','')}",
            "roll_up": f"Roll-Up: {data.get('from_level','')} → {data.get('to_level','')}",
            "yoy_growth": "Year-over-Year Growth",
            "mom_change": "Month-over-Month Change",
            "profit_margins": "Profit Margin Analysis",
            "top_n": f"Top {data.get('n', '')} by {data.get('measure', '')}",
            "compare_periods": "Period Comparison",
            "revenue_share": "Revenue Share Analysis",
        }
        return label_map.get(op, op.replace("_", " ").title())
