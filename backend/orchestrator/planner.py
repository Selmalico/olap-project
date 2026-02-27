"""
Orchestrator — plan_and_execute()
──────────────────────────────────
Coordinates the 7-agent pipeline.

All seven agents are real implementations (no phantom imports):
  dimension_navigator  → DimensionNavigatorAgent
  cube_operations      → CubeOperationsAgent
  kpi_calculator       → KPICalculatorAgent
  report_generator     → ReportGeneratorAgent
  visualization_agent  → VisualizationAgent
  anomaly_detection    → AnomalyDetectionAgent
  executive_summary    → ExecutiveSummaryAgent

The IntentDetector provides a fast rule-based routing signal that enriches
the LLM planner's context and acts as a complete fallback when no LLM key
is configured.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Any

from agents.dimension_navigator import DimensionNavigatorAgent
from agents.cube_operations import CubeOperationsAgent
from agents.kpi_calculator import KPICalculatorAgent
from agents.report_generator import ReportGeneratorAgent
from agents.visualization_agent import VisualizationAgent
from agents.anomaly_detection import AnomalyDetectionAgent
from agents.executive_summary import ExecutiveSummaryAgent
from orchestrator.context_manager import add_turn
from orchestrator.intent_detector import IntentDetector

logger = logging.getLogger("selma")

# ── Anthropic client (optional) ───────────────────────────────────────────────
_client = None
try:
    from anthropic import Anthropic
    _api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not _api_key:
        try:
            from config import settings
            _api_key = settings.anthropic_api_key
        except Exception:
            pass
    if _api_key:
        _client = Anthropic(api_key=_api_key)
        logger.info("Anthropic client enabled for orchestrator planner")
except Exception as e:
    logger.info("Anthropic client not available: %s", e)

_intent_detector = IntentDetector()

AGENTS: dict[str, Any] = {
    "dimension_navigator": DimensionNavigatorAgent(),
    "cube_operations":     CubeOperationsAgent(),
    "kpi_calculator":      KPICalculatorAgent(),
    "report_generator":    ReportGeneratorAgent(),
    "visualization_agent": VisualizationAgent(),
    "anomaly_detection":   AnomalyDetectionAgent(),
    "executive_summary":   ExecutiveSummaryAgent(),
}

PLANNER_SYSTEM = """You are an OLAP Query Planner. Analyze the user's query and return a routing plan.

Available agents and when to use them:
- dimension_navigator: when query mentions drill-down, roll-up, "by quarter", "by month", hierarchy navigation
- cube_operations: when query has filters like "only 2024", "in Europe", "Electronics category"
- kpi_calculator: when query asks for growth, comparison, YoY, MoM, top N, rankings, margins
- report_generator: ALWAYS include -- formats results
- visualization_agent: ALWAYS include -- determines best chart
- anomaly_detection: include when comparing trends or when user asks about unusual patterns
- executive_summary: ALWAYS include -- writes C-suite narrative

Return ONLY valid JSON:
{
  "intent": "drill_down|roll_up|slice|dice|kpi|compare|aggregate|pivot",
  "agents": ["agent1", "agent2", "report_generator", "visualization_agent", "executive_summary"],
  "parameters": {
    "filters": {},
    "drill_dimension": "",
    "drill_level": "",
    "kpi_type": "",
    "top_n": null
  },
  "follow_up_questions": [
    "Suggested follow-up question 1?",
    "Suggested follow-up question 2?",
    "Suggested follow-up question 3?"
  ]
}"""


def plan_and_execute(
    query: str,
    history: list,
    conversation_id: str | None = None,
) -> dict:
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # Rule-based intent detection (always runs, enriches LLM context)
    intent_obj = _intent_detector.detect(query, history)

    # Step 1: Get routing plan (LLM or rule-based fallback)
    plan = _get_plan(query, history, intent_obj)

    # Step 2: Execute agents in sequence, passing accumulated data forward
    results: list[dict] = []
    accumulated_data: list[dict] = []
    accumulated_anomalies: list[str] = []
    agent_names_used: list[str] = []

    for agent_name in plan.get("agents", []):
        if agent_name not in AGENTS:
            continue
        agent = AGENTS[agent_name]
        params: dict[str, Any] = {
            **plan.get("parameters", {}),
            "data": accumulated_data,
            "anomalies": accumulated_anomalies,
            "kpis": {},
            "operation": intent_obj.get("intent", ""),
        }
        try:
            result = agent.run(query, params)
            if result.get("data"):
                accumulated_data = result["data"]
            if result.get("anomalies"):
                accumulated_anomalies = result["anomalies"]
            results.append({"agent_name": agent_name, **result})
            agent_names_used.append(agent_name)
        except Exception as e:
            logger.warning("Agent %s failed: %s", agent_name, e)
            results.append({"agent_name": agent_name, "error": str(e), "data": None})

    # Step 3: Ensure executive summary always runs with full context
    if "executive_summary" not in agent_names_used and accumulated_data:
        try:
            summary_result = AGENTS["executive_summary"].run(
                query,
                {"data": accumulated_data, "kpis": {}, "anomalies": accumulated_anomalies},
            )
            results.append({"agent_name": "executive_summary", **summary_result})
            agent_names_used.append("executive_summary")
        except Exception as e:
            logger.warning("ExecutiveSummary fallback failed: %s", e)

    exec_summary = next(
        (r.get("narrative") for r in results if r.get("agent_name") == "executive_summary"),
        None,
    )

    # Step 4: Persist conversation turn
    add_turn(conversation_id, "user", query)
    add_turn(conversation_id, "assistant", exec_summary or "Analysis complete.")

    return {
        "conversation_id": conversation_id,
        "agents_used": agent_names_used,
        "results": results,
        "executive_summary": exec_summary,
        "follow_up_questions": plan.get("follow_up_questions", []),
        "intent": intent_obj,
    }


def _get_plan(query: str, history: list, intent_obj: dict) -> dict:
    """Use LLM for routing plan when available; otherwise use rule-based plan."""
    if _client:
        try:
            plan_msg = (
                f"User query: {query}\n"
                f"Detected intent: {intent_obj.get('intent')} "
                f"(confidence {intent_obj.get('confidence', 0):.2f})\n"
                f"Conversation turns so far: {len(history)}"
            )
            resp = _client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1000,
                system=PLANNER_SYSTEM,
                messages=[{"role": "user", "content": plan_msg}],
            )
            plan_text = resp.content[0].text
            match = re.search(r"\{.*\}", plan_text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.warning("LLM planner failed, using rule-based fallback: %s", e)

    return _rule_based_plan(intent_obj)


def _rule_based_plan(intent_obj: dict) -> dict:
    """Build an agent sequence from the detected intent without any LLM call."""
    intent = intent_obj.get("intent", "top_n")

    intent_to_primary: dict[str, list[str]] = {
        "drill_down":         ["dimension_navigator"],
        "roll_up":            ["dimension_navigator"],
        "drill_through":      ["dimension_navigator"],
        "describe_hierarchy": ["dimension_navigator"],
        "slice":              ["cube_operations"],
        "dice":               ["cube_operations"],
        "pivot":              ["cube_operations"],
        "compare_periods":    ["kpi_calculator", "anomaly_detection"],
        "yoy_growth":         ["kpi_calculator", "anomaly_detection"],
        "mom_change":         ["kpi_calculator"],
        "ytd_revenue":        ["kpi_calculator"],
        "rolling_avg":        ["kpi_calculator"],
        "top_n":              ["kpi_calculator"],
        "profit_margins":     ["kpi_calculator"],
        "revenue_share":      ["kpi_calculator"],
        "aggregate":          ["kpi_calculator"],
    }
    primary = intent_to_primary.get(intent, ["kpi_calculator"])
    agents = primary + ["report_generator", "visualization_agent", "executive_summary"]

    follow_up_map: dict[str, list[str]] = {
        "drill_down":      ["Roll up to see the bigger picture", "Show profit margins at this level", "Which sub-group has the highest revenue?"],
        "roll_up":         ["Drill down for more detail", "Compare year-over-year at this level", "Show revenue share by region"],
        "drill_through":   ["Summarise these transactions by category", "Show top 5 countries by revenue", "Drill down to quarterly level"],
        "compare_periods": ["Show YoY growth by category", "Which region drove the biggest change?", "Drill down into the best-performing quarter"],
        "yoy_growth":      ["Show month-over-month trend for 2024", "Which category has the highest YoY growth?", "Compare Q3 vs Q4 this year"],
        "mom_change":      ["Show YoY growth for the same metric", "Which region had the biggest monthly swing?", "Show YTD cumulative revenue for 2024"],
        "ytd_revenue":     ["Compare YTD vs same period last year", "Show month-over-month within this year", "Which category drives the most YTD revenue?"],
        "rolling_avg":     ["Show raw monthly data alongside the rolling average", "Compare 3-month vs 6-month rolling averages", "Which month had the biggest deviation from the trend?"],
        "top_n":           ["Show profit margins for these top performers", "Compare these results with last year", "Drill into the top country by region"],
        "profit_margins":  ["Which subcategory has the lowest margin?", "Show revenue vs profit for these groups", "Compare margins YoY"],
        "revenue_share":   ["Show top 5 by absolute revenue", "Compare revenue share between 2023 and 2024", "Drill down to country level"],
        "slice":           ["Add another filter to narrow down", "Show YoY growth for this slice", "Which sub-group performs best here?"],
        "dice":            ["Show profit margins for this combination", "Drill down within this filtered view", "Compare with a different time period"],
        "pivot":           ["Show the same pivot for profit", "Which cell in the matrix has the highest value?", "Compare this pivot with last year"],
        "aggregate":       ["Break this down by category", "Show YoY growth", "Which region contributes the most?"],
    }
    follow_ups = follow_up_map.get(intent, [
        "Show revenue breakdown by region",
        "Compare 2023 vs 2024 performance",
        "Which segment has the highest profit margin?",
    ])

    return {
        "intent": intent,
        "agents": agents,
        "parameters": intent_obj.get("params", {}),
        "follow_up_questions": follow_ups,
    }
