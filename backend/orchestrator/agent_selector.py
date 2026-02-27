"""
Agent Selector
──────────────
Maps a classified intent to an ordered list of execution steps.

Each step is a dict:
    {
        "agent":  str,   # "kpi" | "cube" | "nav" | "report"
        "method": str,   # method name on the agent instance
        "params": dict,  # kwargs to pass
        "label":  str,   # human-readable label for the step
    }

The caller (PlannerAgent) executes steps in order, passing each result
forward through the data-flow context so later steps can reference it.
"""

from __future__ import annotations

from typing import Any

from .intent_detector import (
    INTENT_COMPARE, INTENT_YOY, INTENT_MOM, INTENT_TOP_N,
    INTENT_PROFIT_MARGINS, INTENT_REVENUE_SHARE,
    INTENT_DRILL_DOWN, INTENT_ROLL_UP,
    INTENT_SLICE, INTENT_DICE, INTENT_PIVOT,
    INTENT_AGGREGATE, INTENT_RANK_ALL, INTENT_DESCRIBE,
    INTENT_UNKNOWN,
)


# ── Step builder helpers ──────────────────────────────────────────────────────

def _kpi(method: str, params: dict, label: str) -> dict:
    return {"agent": "kpi", "method": method, "params": params, "label": label}


def _cube(method: str, params: dict, label: str) -> dict:
    return {"agent": "cube", "method": method, "params": params, "label": label}


def _nav(method: str, params: dict, label: str) -> dict:
    return {"agent": "nav", "method": method, "params": params, "label": label}


def _report(method: str, params: dict, label: str) -> dict:
    return {"agent": "report", "method": method, "params": params, "label": label}


# ── AgentSelector class ───────────────────────────────────────────────────────

class AgentSelector:
    """
    Translates a structured intent (from IntentDetector) into an ordered
    list of agent execution steps.

    Multi-step flows
    ────────────────
    Some intents produce a *chain* of steps, e.g.:
      "Compare Q3 vs Q4, identify best region, drill into it" →
        [compare_periods, top_n(region), drill_down(region)]

    The selector embeds chain logic for the example flow specified in the
    project requirements:
      Step 1 – Compare Q3 vs Q4
      Step 2 – Identify best region  (top_n by region)
      Step 3 – Drill into that region (drill_down with region filter)
      Step 4 – Generate report        (executive_summary)

    Secondary intents from IntentDetector are appended after the primary steps.
    """

    def select(self, intent_obj: dict[str, Any]) -> list[dict]:
        """
        Return an ordered list of execution steps for *intent_obj*.

        Parameters
        ----------
        intent_obj : output of IntentDetector.detect()
        """
        intent    = intent_obj["intent"]
        params    = intent_obj["params"]
        secondary = intent_obj.get("secondary", [])

        primary_steps = self._primary_steps(intent, params)
        secondary_steps = self._secondary_steps(secondary, params, already={intent})

        return primary_steps + secondary_steps

    # ── Primary step mapping ──────────────────────────────────────────────────

    def _primary_steps(self, intent: str, params: dict) -> list[dict]:

        if intent == INTENT_COMPARE:
            steps = [
                _kpi("compare_periods", params, "Compare periods"),
            ]
            # If the query also implies finding the top region/category,
            # add an automatic top_n step so the user sees which dimension led
            if params.get("group_by"):
                steps.append(_kpi("top_n", {
                    "measure":  params.get("measure", "revenue"),
                    "n":        5,
                    "group_by": params["group_by"],
                    "filters":  params.get("filters", {}),
                }, f"Top 5 by {params['group_by']}"))
            return steps

        if intent == INTENT_YOY:
            return [_kpi("yoy_growth", params, "Year-over-year growth")]

        if intent == INTENT_MOM:
            return [_kpi("mom_change", params, "Month-over-month change")]

        if intent == INTENT_TOP_N:
            return [_kpi("top_n", params, f"Top {params.get('n', 5)} by {params.get('group_by', 'country')}")]

        if intent == INTENT_RANK_ALL:
            return [_kpi("rank_all", params, f"Full ranking by {params.get('group_by', 'country')}")]

        if intent == INTENT_PROFIT_MARGINS:
            return [_kpi("profit_margins", params, "Profit margin analysis")]

        if intent == INTENT_REVENUE_SHARE:
            return [_kpi("revenue_share", params, "Revenue share breakdown")]

        if intent == INTENT_AGGREGATE:
            return [_kpi("aggregate", params, "Aggregate metrics")]

        if intent == INTENT_DRILL_DOWN:
            return [_nav("drill_down", params, f"Drill down: {params.get('from_level')} → {params.get('to_level')}")]

        if intent == INTENT_ROLL_UP:
            return [_nav("roll_up", params, f"Roll up: {params.get('from_level')} → {params.get('to_level')}")]

        if intent == INTENT_DESCRIBE:
            return [_nav("describe_hierarchy", params, f"Hierarchy: {params.get('hierarchy')}")]

        if intent == INTENT_SLICE:
            return [_cube("slice", params, f"Slice: {params.get('dimension')} = {params.get('value')}")]

        if intent == INTENT_DICE:
            return [_cube("dice", params, f"Dice: {params.get('filters')}")]

        if intent == INTENT_PIVOT:
            return [_cube("pivot", params, f"Pivot: {params.get('rows')} × {params.get('columns')}")]

        # Default / unknown
        return [_kpi("top_n", {"measure": "revenue", "n": 5, "group_by": "region"}, "Top 5 regions by revenue")]

    # ── Secondary steps ───────────────────────────────────────────────────────

    def _secondary_steps(
        self,
        secondary: list[str],
        primary_params: dict,
        already: set[str],
    ) -> list[dict]:
        steps: list[dict] = []
        for intent in secondary:
            if intent in already:
                continue
            already.add(intent)
            if intent == INTENT_TOP_N:
                dim = primary_params.get("group_by", "region")
                steps.append(_kpi("top_n", {
                    "measure":  primary_params.get("measure", "revenue"),
                    "n":        5,
                    "group_by": dim,
                    "filters":  primary_params.get("filters", {}),
                }, f"Identify best {dim}"))
            elif intent == INTENT_DRILL_DOWN:
                steps.append(_nav("drill_down", {
                    "hierarchy":  "time",
                    "from_level": "year",
                    "to_level":   "quarter",
                    "filters":    primary_params.get("filters", {}),
                }, "Drill down to quarter"))
            elif intent == INTENT_PROFIT_MARGINS:
                steps.append(_kpi("profit_margins", {
                    "group_by": primary_params.get("group_by", "category"),
                    "filters":  primary_params.get("filters", {}),
                }, "Profit margin breakdown"))
            elif intent == INTENT_YOY:
                steps.append(_kpi("yoy_growth", {
                    "measure": primary_params.get("measure", "revenue"),
                    "filters": primary_params.get("filters", {}),
                }, "Year-over-year comparison"))
            elif intent == INTENT_COMPARE:
                steps.append(_kpi("compare_periods", {
                    "period_a": {"year": 2023},
                    "period_b": {"year": 2024},
                    "measure":  primary_params.get("measure", "revenue"),
                }, "Period comparison"))
        return steps

    # ── Chained-flow builder (used by PlannerAgent for multi-step queries) ────

    def build_chained_flow(
        self,
        compare_params: dict,
        drill_dimension: str = "region",
    ) -> list[dict]:
        """
        Build the four-step chain described in the project requirements:
          1. Compare Q3 vs Q4
          2. Identify best region (top_n)
          3. Drill into that region
          4. Generate report

        This is called when the query matches the "compare → identify → drill → report"
        pattern.  The drill step carries a placeholder filter `{BEST_<dim>}` that
        PlannerAgent replaces with the actual winner from step 2 at runtime.
        """
        measure = compare_params.get("measure", "revenue")
        base_filters = compare_params.get("filters", {})

        return [
            _kpi("compare_periods", compare_params, "Step 1 – Compare periods"),
            _kpi("top_n", {
                "measure":  measure,
                "n":        1,
                "group_by": drill_dimension,
                "filters":  base_filters,
            }, f"Step 2 – Identify best {drill_dimension}"),
            # Placeholder: PlannerAgent injects the winner value before calling
            _nav("drill_down", {
                "hierarchy":  "geography" if drill_dimension == "region" else "product",
                "from_level": drill_dimension,
                "to_level":   "country" if drill_dimension == "region" else "subcategory",
                "filters":    {drill_dimension: f"{{BEST_{drill_dimension.upper()}}}"},
            }, f"Step 3 – Drill into best {drill_dimension}"),
            # Final report step — params filled by PlannerAgent from prior results
            _report("executive_summary", {}, "Step 4 – Executive report"),
        ]

    def detect_chained_flow(self, query: str, intent_obj: dict) -> bool:
        """
        Return True when the query implies the full
        compare → identify → drill → report chain.
        """
        import re
        q = query.lower()
        has_compare  = bool(re.search(r"\bvs\.?\b|\bcompare\b|\bversus\b", q))
        has_identify = bool(re.search(r"\bbest\b|\btop\b|\bhighest\b|\bidentif", q))
        has_drill    = bool(re.search(r"\bdrill\b|\bdetail\b|\bbreak\s*down\b|\binto\b", q))
        return has_compare and (has_identify or has_drill)
