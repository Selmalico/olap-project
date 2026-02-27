"""
Executive Summary Agent
────────────────────────
Generates a 3-sentence C-suite narrative from analysis results.

Structure
─────────
  1. What happened  (key metric + direction + magnitude)
  2. What drove it  (top dimension / region / product responsible)
  3. What to watch  (actionable recommendation)

Uses HuggingFace Qwen 2.5 when HUGGINGFACE_TOKEN is set; falls back to
a deterministic heuristic narrative that is still informative.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("selma")


def _fmt_money(v) -> str:
    try:
        f = float(v)
        return f"${f:,.2f}"
    except (TypeError, ValueError):
        return str(v)


def _fmt_pct(v) -> str:
    try:
        f = float(v)
        sign = "+" if f > 0 else ""
        return f"{sign}{f:.1f}%"
    except (TypeError, ValueError):
        return str(v)


class ExecutiveSummaryAgent:
    """
    Produces a concise executive narrative from OLAP result data.
    """

    def __init__(self) -> None:
        self._hf_client = None
        self._model = "Qwen/Qwen2.5-7B-Instruct"

        hf_token = (os.getenv("HUGGINGFACE_TOKEN") or "").strip()
        if hf_token:
            try:
                from huggingface_hub import InferenceClient
                self._hf_client = InferenceClient(model=self._model, token=hf_token)
                logger.info(f"ExecutiveSummary: HuggingFace enabled ({self._model})")
            except Exception as e:
                logger.warning("ExecutiveSummary: HuggingFace init failed: %s", e)

    # ── Public API ────────────────────────────────────────────────────────────

    def summarize(
        self,
        data: dict[str, Any],
        anomalies: list[str] | None = None,
        kpis: dict | None = None,
    ) -> dict[str, Any]:
        """
        Generate a narrative from an agent result dict.

        Parameters
        ----------
        data      : raw agent result (must have 'operation' and 'rows')
        anomalies : optional list of anomaly strings from AnomalyDetectionAgent
        kpis      : optional KPI dict for context
        """
        heuristic = self._heuristic(data, anomalies or [])

        if self._hf_client:
            try:
                prompt = (
                    "You are a senior BI analyst writing a 3-sentence executive summary. "
                    "Sentence 1: what happened (key metric + direction + magnitude). "
                    "Sentence 2: what drove it (top segment/region/product). "
                    "Sentence 3: what to watch or do next (actionable). "
                    "Use specific numbers. Return only the 3-sentence paragraph, no JSON.\n\n"
                    f"Data (JSON): {json.dumps(data, default=str)[:2000]}\n"
                    f"Anomalies: {anomalies or []}"
                )
                response = self._hf_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                )
                text = response.choices[0].message.content.strip()
                if text:
                    return {"narrative": text}
            except Exception as e:
                logger.warning("ExecutiveSummary HF call failed: %s", e)

        return {"narrative": heuristic}

    def run(self, query: str, params: dict) -> dict[str, Any]:
        """Agent interface used by orchestrator/planner.py."""
        data_raw = params.get("data", [])
        anomalies = params.get("anomalies", [])
        kpis = params.get("kpis", {})

        # Normalise data_raw into a result dict
        if isinstance(data_raw, list):
            result_dict: dict[str, Any] = {"operation": "query", "rows": data_raw}
        elif isinstance(data_raw, dict):
            result_dict = data_raw
        else:
            result_dict = {"operation": "query", "rows": []}

        return self.summarize(result_dict, anomalies=anomalies, kpis=kpis)

    # ── Heuristic narrative ───────────────────────────────────────────────────

    def _heuristic(self, data: dict, anomalies: list[str]) -> str:
        operation = data.get("operation", "")
        if operation == "pivot":
            rows = data.get("rows_list", [])
        else:
            rows = data.get("rows", data.get("rows_list", []))

        if not rows or not isinstance(rows, list):
            return "No data was returned for this query. Try broadening the filters or checking data availability."

        sentences: list[str] = []

        # Sentence 1: What happened
        sentences.append(self._what_happened(operation, rows, data))

        # Sentence 2: What drove it
        driver = self._what_drove_it(operation, rows, data)
        if driver:
            sentences.append(driver)

        # Sentence 3: Recommendation
        rec = self._recommendation(operation, rows, anomalies)
        sentences.append(rec)

        return " ".join(sentences)

    def _what_happened(self, operation: str, rows: list[dict], data: dict) -> str:
        if operation == "yoy_growth":
            measure = data.get("measure", "revenue")
            latest = [r for r in rows if r.get("pct_change") is not None]
            if latest:
                best = max(latest, key=lambda r: float(r.get("pct_change") or 0))
                return (
                    f"Year-over-year {measure} growth reached "
                    f"{_fmt_pct(best.get('pct_change'))} "
                    f"in {best.get('year', 'the latest year')}."
                )
        if operation == "mom_change":
            measure = data.get("measure", "revenue")
            latest = [r for r in rows if r.get("pct_change") is not None]
            if latest:
                last = latest[-1]
                return (
                    f"Month-over-month {measure} changed by "
                    f"{_fmt_pct(last.get('pct_change'))} "
                    f"in {last.get('month_name', last.get('month', 'the latest month'))}."
                )
        if operation == "compare_periods":
            row = rows[0]
            pa = data.get("period_a", {})
            pb = data.get("period_b", {})
            return (
                f"Comparing {pa} vs {pb}: "
                f"{data.get('measure', 'revenue')} changed by "
                f"{_fmt_pct(row.get('pct_change'))} "
                f"({_fmt_money(row.get('value_a'))} → {_fmt_money(row.get('value_b'))})."
            )
        if operation == "top_n":
            top = rows[0]
            return (
                f"The leading {data.get('group_by', 'segment')} by "
                f"{data.get('measure', 'revenue')} is "
                f"{top.get('group_dim')} at {_fmt_money(top.get('metric'))}."
            )
        if operation == "profit_margins":
            best = max(rows, key=lambda r: float(r.get("avg_margin") or 0))
            return (
                f"Profit margin analysis shows {best.get('group_dim')} "
                f"leads with an average margin of {_fmt_pct(best.get('avg_margin'))}."
            )
        if operation in ("drill_down", "roll_up"):
            total = sum(
                float(r.get("total_revenue") or 0) for r in rows
                if isinstance(r.get("total_revenue"), (int, float))
            )
            return (
                f"{'Drill-down' if operation == 'drill_down' else 'Roll-up'} "
                f"to {data.get('to_level', 'next level')} reveals "
                f"total revenue of {_fmt_money(total)} across {len(rows)} groups."
            )
        if operation == "revenue_share":
            top = rows[0] if rows else {}
            return (
                f"Revenue share analysis shows {top.get('group_dim', 'the top segment')} "
                f"accounts for {_fmt_pct(top.get('revenue_share_pct'))} of total revenue."
            )
        # Generic fallback
        return f"The analysis returned {len(rows)} data point(s) for the '{operation}' operation."

    def _what_drove_it(self, operation: str, rows: list[dict], data: dict) -> str | None:
        if operation == "yoy_growth" and len(rows) >= 2:
            valid = [r for r in rows if r.get("pct_change") is not None]
            if valid:
                best = max(valid, key=lambda r: float(r.get("pct_change") or 0))
                worst = min(valid, key=lambda r: float(r.get("pct_change") or 0))
                label = best.get("group", best.get("year", ""))
                return (
                    f"The strongest performer was {label} "
                    f"({_fmt_pct(best.get('pct_change'))} growth), "
                    f"while {worst.get('group', worst.get('year', 'the weakest'))} "
                    f"lagged at {_fmt_pct(worst.get('pct_change'))}."
                )
        if operation == "top_n" and len(rows) >= 2:
            top = rows[0]
            second = rows[1]
            return (
                f"{top.get('group_dim')} outperformed the runner-up "
                f"{second.get('group_dim')} by "
                f"{_fmt_money(float(top.get('metric', 0)) - float(second.get('metric', 0)))}."
            )
        if operation == "profit_margins" and len(rows) >= 2:
            worst = min(rows, key=lambda r: float(r.get("avg_margin") or 0))
            return (
                f"The lowest margin was recorded in {worst.get('group_dim')} "
                f"at {_fmt_pct(worst.get('avg_margin'))}, indicating potential pricing pressure."
            )
        return None

    def _recommendation(self, operation: str, rows: list[dict], anomalies: list[str]) -> str:
        if anomalies:
            return (
                f"Note {len(anomalies)} statistical anomaly(ies) detected — "
                "investigate before drawing conclusions."
            )
        recs = {
            "yoy_growth": "Monitor the declining segments closely and consider targeted investment to reverse the trend.",
            "mom_change": "Review seasonal patterns and align inventory and marketing spend accordingly.",
            "compare_periods": "Identify the operational changes between periods to replicate successes or address shortfalls.",
            "top_n": "Prioritise resources toward the top performers while investigating under-performers for improvement opportunities.",
            "profit_margins": "Review pricing and cost structure for low-margin segments to improve overall profitability.",
            "drill_down": "Use this granular view to identify specific sub-segments that need attention.",
            "roll_up": "Compare the aggregated view against targets to assess strategic alignment.",
            "revenue_share": "Consider rebalancing the portfolio to reduce over-concentration in a single segment.",
            "slice": "Apply additional dimension filters to identify the root cause of the observed pattern.",
            "dice": "Cross-reference with other dimensions to isolate the primary driver of performance.",
            "pivot": "Use the pivot matrix to spot underperforming intersections and prioritise corrective actions.",
        }
        return recs.get(operation, "Continue monitoring KPIs and validate findings against operational data.")
