"""
Anomaly Detection Agent
────────────────────────
Detects statistical outliers using Z-score analysis (no LLM calls needed).

Spec
────
  • Z-score threshold : 2.5
  • Maximum reported  : 5 anomalies (most extreme first)
  • Minimum rows      : 4 (too few rows → no meaningful statistics)
  • Analyses all numeric columns in the data
"""

from __future__ import annotations

import math
from typing import Any


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


class AnomalyDetectionAgent:
    """
    Detects statistical outliers in OLAP result rows using Z-score analysis.
    Does not make any LLM or DB calls.
    """

    Z_THRESHOLD = 2.5
    MAX_ANOMALIES = 5
    MIN_ROWS = 4

    def detect(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyse *rows* for numeric outliers.

        Parameters
        ----------
        rows : list of dicts (e.g. result["rows"] from any agent)
        """
        if not rows or len(rows) < self.MIN_ROWS:
            return {
                "anomalies": [],
                "flagged_rows": [],
                "columns_analyzed": [],
            }

        # Identify numeric columns
        numeric_cols = [
            col for col in rows[0].keys()
            if self._is_numeric_col(rows, col)
        ]

        if not numeric_cols:
            return {
                "anomalies": [],
                "flagged_rows": [],
                "columns_analyzed": [],
            }

        anomaly_hits: list[tuple[float, str]] = []  # (z_score, message)
        flagged_indices: set[int] = set()

        for col in numeric_cols:
            values = []
            indices = []
            for i, row in enumerate(rows):
                v = row.get(col)
                if isinstance(v, (int, float)) and not math.isnan(v):
                    values.append(float(v))
                    indices.append(i)

            if len(values) < self.MIN_ROWS:
                continue

            mean = _mean(values)
            std = _std(values, mean)

            if std == 0:
                continue

            for list_idx, (row_idx, val) in enumerate(zip(indices, values)):
                z = abs(val - mean) / std
                if z > self.Z_THRESHOLD:
                    pct_from_mean = ((val - mean) / mean * 100) if mean != 0 else 0
                    # Find a label for this row
                    row = rows[row_idx]
                    label = self._row_label(row, col)
                    msg = (
                        f"{col} for {label}: "
                        f"{val:,.2f} is {abs(pct_from_mean):.1f}% from mean "
                        f"({mean:,.2f}), Z={z:.2f}"
                    )
                    anomaly_hits.append((z, msg))
                    flagged_indices.add(row_idx)

        # Sort by Z-score descending, cap at MAX_ANOMALIES
        anomaly_hits.sort(key=lambda x: x[0], reverse=True)
        top = anomaly_hits[: self.MAX_ANOMALIES]

        return {
            "anomalies": [msg for _, msg in top],
            "flagged_rows": sorted(flagged_indices),
            "columns_analyzed": numeric_cols,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_numeric_col(self, rows: list[dict], col: str) -> bool:
        """Return True if the column is predominantly numeric (non-ID)."""
        # Skip obvious identifier / label columns
        skip_keywords = ("id", "name", "label", "rank", "order", "period")
        if any(kw in col.lower() for kw in skip_keywords):
            return False
        sample = [r.get(col) for r in rows[:10] if r.get(col) is not None]
        return bool(sample) and all(isinstance(v, (int, float)) for v in sample)

    def _row_label(self, row: dict, value_col: str) -> str:
        """Pick the most descriptive label field from a row."""
        for candidate in ("group_dim", "region", "country", "category",
                          "subcategory", "customer_segment", "year",
                          "month_name", "quarter"):
            if candidate in row and candidate != value_col:
                return str(row[candidate])
        return str(list(row.values())[0])

    def run(self, query: str, params: dict) -> dict[str, Any]:
        """Agent interface used by orchestrator/planner.py."""
        data = params.get("data", [])
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = data.get("rows", [])
        else:
            rows = []
        return self.detect(rows)
