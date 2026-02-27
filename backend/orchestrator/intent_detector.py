"""
Intent Detector
───────────────
Classifies a natural-language BI query into a structured intent object
without requiring an LLM.  The LLM planner uses this as a fast first-pass;
the keyword fallback router uses it exclusively.

Intent schema
─────────────
{
    "intent":      str,          # primary operation name (see INTENT_* constants)
    "confidence":  float,        # 0.0 – 1.0
    "params":      dict,         # extracted parameters ready for agent dispatch
    "secondary":   list[str],    # additional intents implied by the query
    "is_followup": bool,         # True when query refers to prior context
    "context_refs": list[str],   # context slots referenced ("that region", "same period", …)
}
"""

from __future__ import annotations

import re
from typing import Any

# ── Intent constants ──────────────────────────────────────────────────────────

INTENT_COMPARE        = "compare_periods"
INTENT_YOY            = "yoy_growth"
INTENT_MOM            = "mom_change"
INTENT_TOP_N          = "top_n"
INTENT_PROFIT_MARGINS = "profit_margins"
INTENT_REVENUE_SHARE  = "revenue_share"
INTENT_DRILL_DOWN     = "drill_down"
INTENT_ROLL_UP        = "roll_up"
INTENT_SLICE          = "slice"
INTENT_DICE           = "dice"
INTENT_PIVOT          = "pivot"
INTENT_AGGREGATE      = "aggregate"
INTENT_RANK_ALL       = "rank_all"
INTENT_DESCRIBE       = "describe_hierarchy"
INTENT_UNKNOWN        = "top_n"   # safe default

# ── Domain vocabulary ────────────────────────────────────────────────────────

_YEARS = {2022, 2023, 2024}
_QUARTERS = {"q1": 1, "q2": 2, "q3": 3, "q4": 4,
             "quarter 1": 1, "quarter 2": 2, "quarter 3": 3, "quarter 4": 4,
             "first quarter": 1, "second quarter": 2,
             "third quarter": 3, "fourth quarter": 4}

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12,
}

_REGIONS = {"north america", "europe", "asia pacific", "latin america"}
_COUNTRIES = {
    "usa", "canada", "brazil", "mexico", "uk", "germany", "france",
    "italy", "spain", "china", "japan", "india", "australia",
    "south korea", "singapore", "argentina", "colombia",
    # also accept display forms
    "united states", "united kingdom",
}
_CATEGORIES = {"electronics", "furniture", "office supplies", "clothing"}
_SUBCATEGORIES = {
    "phones", "laptops", "tablets", "cameras", "accessories",
    "chairs", "desks", "shelves", "sofas",
    "paper", "binders", "pens", "labels",
    "shirts", "pants", "shoes", "jackets",
}
_SEGMENTS = {"consumer", "corporate", "home office", "small business"}

_MEASURES = {"revenue", "profit", "cost", "quantity", "profit_margin", "margin"}

_HIERARCHY_LEVELS = {
    "year": "time", "quarter": "time", "month": "time",
    "region": "geography", "country": "geography",
    "category": "product", "subcategory": "product",
}

# ── Context-reference markers ─────────────────────────────────────────────────

_FOLLOWUP_MARKERS = [
    r"\bthat\b", r"\bthis\b", r"\bsame\b", r"\bthose\b",
    r"\bthe (above|previous|prior|last|mentioned)\b",
    r"\bdrilling? (into|down)\b",
    r"\bmore detail\b", r"\bbreak (?:it|this|that) down\b",
    r"\bfurther\b",
]
_FOLLOWUP_RE = re.compile("|".join(_FOLLOWUP_MARKERS), re.IGNORECASE)

_CONTEXT_SLOT_PATTERNS = {
    "region":   re.compile(r"\bthat region\b|\bsame region\b", re.I),
    "category": re.compile(r"\bthat category\b|\bsame category\b", re.I),
    "period":   re.compile(r"\bsame period\b|\bthat period\b|\bprevious period\b", re.I),
    "year":     re.compile(r"\bthat year\b|\bsame year\b", re.I),
    "top":      re.compile(r"\btop (?:one|performer|group|result)\b", re.I),
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_years(q: str) -> list[int]:
    return [int(m) for m in re.findall(r"\b(202[2-4])\b", q)]


def _extract_quarter(q: str) -> int | None:
    for label, num in _QUARTERS.items():
        if re.search(rf"\b{re.escape(label)}\b", q, re.I):
            return num
    return None


def _extract_month(q: str) -> int | None:
    for label, num in _MONTHS.items():
        if re.search(rf"\b{re.escape(label)}\b", q, re.I):
            return num
    return None


def _extract_measure(q: str) -> str:
    for m in ("profit_margin", "profit", "revenue", "cost", "quantity"):
        if m.replace("_", " ") in q or m in q:
            return m
    return "revenue"


def _extract_n(q: str) -> int:
    m = re.search(r"\btop\s+(\d+)\b", q, re.I)
    return int(m.group(1)) if m else 5


def _extract_dimension(q: str) -> str | None:
    """Return the first dimension name mentioned in the query."""
    order = ["subcategory", "customer_segment", "category",
             "country", "region", "month", "quarter", "year"]
    for d in order:
        if d.replace("_", " ") in q or d in q:
            return d
    return None


def _extract_filters(q: str) -> dict[str, Any]:
    """Pull explicit filter values from the query text."""
    filters: dict[str, Any] = {}
    years = _extract_years(q)
    if len(years) == 1:
        filters["year"] = years[0]
    qt = _extract_quarter(q)
    if qt:
        filters["quarter"] = qt
    for r in _REGIONS:
        if r in q:
            filters["region"] = r.title()
            break
    for c in _COUNTRIES:
        if re.search(rf"\b{re.escape(c)}\b", q):
            # normalise common variants
            display = {"usa": "USA", "uk": "UK", "united states": "USA",
                       "united kingdom": "UK"}.get(c, c.title())
            filters["country"] = display
            break
    for cat in _CATEGORIES:
        if cat in q:
            filters["category"] = cat.title()
            break
    for sub in _SUBCATEGORIES:
        if re.search(rf"\b{re.escape(sub)}\b", q):
            filters["subcategory"] = sub.title()
            break
    for seg in _SEGMENTS:
        if seg in q:
            filters["customer_segment"] = seg.title()
            break
    return filters


def _period_from_quarter(year: int | None, quarter: int) -> dict:
    p: dict[str, Any] = {"quarter": quarter}
    if year:
        p["year"] = year
    return p


def _build_compare_params(q: str) -> dict:
    """
    Extract period_a / period_b for compare_periods.
    Handles patterns like:
      "Q3 vs Q4", "2023 vs 2024", "Q3 2024 vs Q4 2024",
      "compare first half vs second half"
    """
    years = _extract_years(q)
    # Find all quarter tokens in order of appearance
    quarter_matches = list(re.finditer(
        r"\b(q[1-4]|quarter\s+[1-4]|first quarter|second quarter|third quarter|fourth quarter)\b",
        q, re.I))

    if len(quarter_matches) >= 2:
        qa = _QUARTERS.get(quarter_matches[0].group(0).lower().strip())
        qb = _QUARTERS.get(quarter_matches[1].group(0).lower().strip())
        year_a = years[0] if years else None
        year_b = years[-1] if years else None
        return {
            "period_a": _period_from_quarter(year_a, qa or 3),
            "period_b": _period_from_quarter(year_b, qb or 4),
        }

    if len(years) >= 2:
        return {"period_a": {"year": years[0]}, "period_b": {"year": years[1]}}

    if len(years) == 1:
        qt = _extract_quarter(q)
        if qt:
            other = qt - 1 if qt > 1 else qt + 1
            return {
                "period_a": _period_from_quarter(years[0], min(qt, other)),
                "period_b": _period_from_quarter(years[0], max(qt, other)),
            }
        return {"period_a": {"year": years[0] - 1}, "period_b": {"year": years[0]}}

    # Fallback: most recent two years
    return {"period_a": {"year": 2023}, "period_b": {"year": 2024}}


# ─────────────────────────────────────────────────────────────────────────────
# Main classifier
# ─────────────────────────────────────────────────────────────────────────────

class IntentDetector:
    """
    Rule-based intent classifier for OLAP natural-language queries.

    Usage
    -----
    detector = IntentDetector()
    intent   = detector.detect("Compare Q3 vs Q4 revenue")
    # → {"intent": "compare_periods", "confidence": 0.9, "params": {...}, ...}
    """

    def detect(self, query: str, history: list[dict] | None = None) -> dict[str, Any]:
        """
        Classify *query* and return a structured intent dict.

        Parameters
        ----------
        query   : raw user query string
        history : prior conversation turns (list of {role, content})
        """
        q = query.lower().strip()

        is_followup   = bool(_FOLLOWUP_RE.search(q))
        context_refs  = [slot for slot, pat in _CONTEXT_SLOT_PATTERNS.items()
                         if pat.search(q)]

        intent, confidence, params = self._classify(q)
        secondary = self._secondary_intents(q, intent)

        return {
            "intent":       intent,
            "confidence":   confidence,
            "params":       params,
            "secondary":    secondary,
            "is_followup":  is_followup,
            "context_refs": context_refs,
        }

    # ── Primary classifier ────────────────────────────────────────────────────

    def _classify(self, q: str) -> tuple[str, float, dict]:
        """Return (intent, confidence, params)."""

        # ── Compare / period vs period ───────────────────────────────────────
        if re.search(r"\bvs\.?\b|\bversus\b|\bcompare\b|\bcomparison\b", q):
            params = _build_compare_params(q)
            params["measure"] = _extract_measure(q)
            dim = _extract_dimension(q)
            if dim and dim not in ("year", "quarter", "month"):
                params["group_by"] = dim
            return INTENT_COMPARE, 0.92, params

        # ── Drill down ───────────────────────────────────────────────────────
        if re.search(r"\bdrill\s*(down|into|deeper)\b|\bbreak\s*down\b|\bdetail\b", q):
            params = self._drill_params(q, down=True)
            return INTENT_DRILL_DOWN, 0.90, params

        # ── Roll up ──────────────────────────────────────────────────────────
        if re.search(r"\broll\s*up\b|\baggregate\s*up\b|\bhigher\s*level\b|\bzoom\s*out\b", q):
            params = self._drill_params(q, down=False)
            return INTENT_ROLL_UP, 0.90, params

        # ── YoY ─────────────────────────────────────────────────────────────
        if re.search(r"\byoy\b|\byear.over.year\b|\bannual\s*growth\b|\byearly\s*(trend|growth|change)\b", q):
            group = _extract_dimension(q)
            if group in ("year", "quarter", "month", None):
                group = None
            return INTENT_YOY, 0.92, {
                "measure":  _extract_measure(q),
                "group_by": group,
                "filters":  _extract_filters(q),
            }

        # ── MoM ─────────────────────────────────────────────────────────────
        if re.search(r"\bmom\b|\bmonth.over.month\b|\bmonthly\s*(trend|change|growth)\b", q):
            years = _extract_years(q)
            return INTENT_MOM, 0.92, {
                "measure": _extract_measure(q),
                "year":    years[0] if years else None,
                "filters": _extract_filters(q),
            }

        # ── Top N / Ranking ──────────────────────────────────────────────────
        if re.search(r"\btop\s*\d*\b|\bbest\b|\bhighest\b|\bleading\b|\bworst\b|\blowest\b|\bbottom\b", q):
            ascending = bool(re.search(r"\bworst\b|\blowest\b|\bbottom\b", q))
            dim = _extract_dimension(q)
            return INTENT_TOP_N, 0.88, {
                "measure":   _extract_measure(q),
                "n":         _extract_n(q),
                "group_by":  dim or "country",
                "filters":   _extract_filters(q),
                "ascending": ascending,
            }

        # ── Profit margins ───────────────────────────────────────────────────
        if re.search(r"\bmargin\b|\bprofitability\b|\bprofit\s*margin\b", q):
            dim = _extract_dimension(q)
            return INTENT_PROFIT_MARGINS, 0.88, {
                "group_by": dim or "category",
                "filters":  _extract_filters(q),
            }

        # ── Revenue share / breakdown ────────────────────────────────────────
        if re.search(r"\bshare\b|\bpercentage\b|\bproportion\b|\bbreakdown\b|\bdistribution\b", q):
            dim = _extract_dimension(q)
            return INTENT_REVENUE_SHARE, 0.85, {
                "group_by": dim or "region",
                "filters":  _extract_filters(q),
            }

        # ── Pivot ────────────────────────────────────────────────────────────
        if re.search(r"\bpivot\b|\bcross.?tab\b|\bmatrix\b", q):
            dims = []
            for d in ["region", "category", "year", "quarter", "customer_segment"]:
                if d in q:
                    dims.append(d)
            rows = dims[0] if dims else "region"
            cols = dims[1] if len(dims) > 1 else "year"
            return INTENT_PIVOT, 0.90, {
                "rows":    rows,
                "columns": cols,
                "values":  _extract_measure(q),
                "filters": _extract_filters(q),
            }

        # ── Slice (single filter) ────────────────────────────────────────────
        if re.search(r"\bslice\b|\bfilter\b|\bshow\s*(only|me|just)\b|\bonly\b|\bfor\s+\d{4}\b", q):
            filters = _extract_filters(q)
            if filters:
                # Use the first filter as the slice dimension/value
                dim, val = next(iter(filters.items()))
                remaining = {k: v for k, v in filters.items() if k != dim}
                params: dict[str, Any] = {"dimension": dim, "value": val}
                if remaining:
                    params["filters"] = remaining
                return INTENT_SLICE, 0.85, params
            return INTENT_SLICE, 0.60, {"dimension": "year", "value": 2024}

        # ── Dice (multiple filters) ──────────────────────────────────────────
        if re.search(r"\bdice\b", q):
            return INTENT_DICE, 0.90, {
                "filters":  _extract_filters(q),
                "group_by": [_extract_dimension(q) or "region"],
            }

        # ── Describe hierarchy ───────────────────────────────────────────────
        if re.search(r"\bhierarch\b|\blevels?\b|\bstructure\b|\bwhat\s*(dimensions|levels)\b", q):
            for h in ("time", "geography", "product"):
                if h in q or (h == "time" and any(x in q for x in ("year", "quarter", "month", "date"))):
                    return INTENT_DESCRIBE, 0.85, {"hierarchy": h}
                if h == "geography" and any(x in q for x in ("region", "country")):
                    return INTENT_DESCRIBE, 0.85, {"hierarchy": h}
                if h == "product" and any(x in q for x in ("category", "subcategory")):
                    return INTENT_DESCRIBE, 0.85, {"hierarchy": h}
            return INTENT_DESCRIBE, 0.75, {"hierarchy": "time"}

        # ── Aggregate (explicit SUM/AVG/COUNT) ───────────────────────────────
        if re.search(r"\bsum\b|\baverage\b|\bavg\b|\bcount\b|\btotal\b|\bhow\s*many\b|\bhow\s*much\b", q):
            funcs = []
            if re.search(r"\bsum\b|\btotal\b", q):
                funcs.append("SUM")
            if re.search(r"\baverage\b|\bavg\b|\bmean\b", q):
                funcs.append("AVG")
            if re.search(r"\bcount\b|\bhow\s*many\b", q):
                funcs.append("COUNT")
            if not funcs:
                funcs = ["SUM"]
            dim = _extract_dimension(q)
            return INTENT_AGGREGATE, 0.82, {
                "measures":  [_extract_measure(q)],
                "functions": funcs,
                "group_by":  dim,
                "filters":   _extract_filters(q),
            }

        # ── Default: top revenue by region ──────────────────────────────────
        return INTENT_UNKNOWN, 0.40, {
            "measure":  "revenue",
            "n":        5,
            "group_by": "region",
            "filters":  {},
        }

    # ── Drill / roll param builder ────────────────────────────────────────────

    def _drill_params(self, q: str, down: bool) -> dict:
        """Infer hierarchy + from/to levels for drill_down / roll_up."""
        # Collect all hierarchy levels mentioned
        mentioned = [lvl for lvl in _HIERARCHY_LEVELS if lvl in q]

        if len(mentioned) >= 2:
            hierarchy = _HIERARCHY_LEVELS[mentioned[0]]
            if down:
                from_level, to_level = mentioned[0], mentioned[1]
            else:
                from_level, to_level = mentioned[1], mentioned[0]
        elif len(mentioned) == 1:
            hierarchy = _HIERARCHY_LEVELS[mentioned[0]]
            lvl = mentioned[0]
            time_order = ["year", "quarter", "month"]
            geo_order = ["region", "country"]
            prod_order = ["category", "subcategory"]
            for order in (time_order, geo_order, prod_order):
                if lvl in order:
                    idx = order.index(lvl)
                    if down and idx < len(order) - 1:
                        from_level, to_level = order[idx], order[idx + 1]
                    elif not down and idx > 0:
                        from_level, to_level = order[idx], order[idx - 1]
                    else:
                        from_level, to_level = order[idx], order[idx]
                    break
            else:
                from_level, to_level = lvl, lvl
        else:
            # Default: drill down time year→quarter
            hierarchy = "time"
            from_level, to_level = ("year", "quarter") if down else ("month", "year")

        return {
            "hierarchy":  hierarchy,
            "from_level": from_level,
            "to_level":   to_level,
            "filters":    _extract_filters(q),
        }

    # ── Secondary intents ─────────────────────────────────────────────────────

    def _secondary_intents(self, q: str, primary: str) -> list[str]:
        """
        Identify additional operations implied alongside the primary intent.
        E.g. "Compare Q3 vs Q4 and identify the best region" → secondary: [top_n]
        """
        secondary: list[str] = []

        if primary != INTENT_COMPARE and re.search(r"\bvs\.?\b|\bcompare\b", q):
            secondary.append(INTENT_COMPARE)

        if primary != INTENT_TOP_N and re.search(
                r"\bbest\b|\bhighest\b|\btop\b|\bleading\b|\bidentif", q):
            secondary.append(INTENT_TOP_N)

        if primary not in (INTENT_DRILL_DOWN, INTENT_ROLL_UP) and re.search(
                r"\bdrill\b|\bbreak\s*down\b|\bdetail\b", q):
            secondary.append(INTENT_DRILL_DOWN)

        if primary != INTENT_PROFIT_MARGINS and re.search(r"\bmargin\b|\bprofitability\b", q):
            secondary.append(INTENT_PROFIT_MARGINS)

        if primary != INTENT_YOY and re.search(r"\byoy\b|\byear.over.year\b", q):
            secondary.append(INTENT_YOY)

        return secondary
