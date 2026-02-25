"""
Planner / Orchestrator Agent
─────────────────────────────
Uses Hugging Face (Qwen 2.5) function-calling to:
  1. Parse the user's natural language query
  2. Identify intent and extract parameters
  3. Route to one or more specialist agents
  4. Aggregate results and call the Report Generator

Falls back to a keyword-based router when HUGGINGFACE_TOKEN is not set.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env from backend directory (same as main.py) so key is set when this module is imported first
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")

logger = logging.getLogger("selma")

from .cube_operations import CubeOperationsAgent
from .dimension_navigator import DimensionNavigatorAgent
from .kpi_calculator import KPICalculatorAgent
from .report_generator import ReportGeneratorAgent

_cube = CubeOperationsAgent()
_nav = DimensionNavigatorAgent()
_kpi = KPICalculatorAgent()
_rpt = ReportGeneratorAgent()

# ── Tool definitions sent to LLM ──────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "drill_down",
            "description": "Drill down a hierarchy to a finer level (e.g. year → quarter → month, region → country, category → subcategory).",
            "parameters": {
                "type": "object",
                "properties": {
                    "hierarchy": {"type": "string", "enum": ["time", "geography", "product"]},
                    "from_level": {"type": "string"},
                    "to_level": {"type": "string"},
                    "filters": {"type": "object"},
                },
                "required": ["hierarchy", "from_level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roll_up",
            "description": "Roll up a hierarchy to a coarser level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hierarchy": {"type": "string", "enum": ["time", "geography", "product"]},
                    "from_level": {"type": "string"},
                    "to_level": {"type": "string"},
                    "filters": {"type": "object"},
                },
                "required": ["hierarchy", "from_level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "slice",
            "description": "Slice the sales cube by one dimension (e.g. show only 2024, or only Electronics).",
            "parameters": {
                "type": "object",
                "properties": {
                    "dimension": {"type": "string"},
                    "value": {},
                    "group_by": {"type": "array", "items": {"type": "string"}},
                    "measures": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["dimension", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dice",
            "description": "Dice the cube by multiple dimension filters simultaneously.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filters": {"type": "object"},
                    "group_by": {"type": "array", "items": {"type": "string"}},
                    "measures": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["filters"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pivot",
            "description": "Pivot the cube across two dimensions (rows × columns) for a measure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rows": {"type": "string"},
                    "columns": {"type": "string"},
                    "values": {"type": "string"},
                    "filters": {"type": "object"},
                    "top_n": {"type": "integer"},
                },
                "required": ["rows", "columns"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "yoy_growth",
            "description": "Calculate year-over-year growth for a measure. Use group_by ONLY for dimension names (like 'category'), never for values (like 'Electronics').",
            "parameters": {
                "type": "object",
                "properties": {
                    "measure": {"type": "string", "enum": ["revenue", "profit", "quantity", "profit_margin"], "default": "revenue"},
                    "group_by": {"type": "string", "enum": ["region", "country", "category", "subcategory", "customer_segment"]},
                    "filters": {
                        "type": "object",
                        "description": "Filters to apply, e.g. {'category': 'Office Supplies'}"
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mom_change",
            "description": "Calculate month-over-month change for a measure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "measure": {"type": "string", "default": "revenue"},
                    "year": {"type": "integer"},
                    "filters": {"type": "object"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "profit_margins",
            "description": "Return profit margins broken down by a dimension.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {"type": "string", "default": "category"},
                    "filters": {"type": "object"},
                    "sort_desc": {"type": "boolean", "default": True},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_n",
            "description": "Return top (or bottom) N entries by a measure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "measure": {"type": "string", "default": "revenue"},
                    "n": {"type": "integer", "default": 5},
                    "group_by": {"type": "string", "default": "country"},
                    "filters": {"type": "object"},
                    "ascending": {"type": "boolean", "default": False},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_periods",
            "description": "Compare two time periods (e.g. Q3 vs Q4 2024, or 2023 vs 2024).",
            "parameters": {
                "type": "object",
                "properties": {
                    "period_a": {"type": "object"},
                    "period_b": {"type": "object"},
                    "measure": {"type": "string", "default": "revenue"},
                    "group_by": {"type": "string"},
                },
                "required": ["period_a", "period_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "revenue_share",
            "description": "Show each group's percentage share of total revenue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {"type": "string", "default": "region"},
                    "filters": {"type": "object"},
                },
            },
        },
    },
]

SYSTEM_PROMPT = """You are an expert OLAP analyst for a Global Retail Sales data warehouse.
The star schema has: fact_sales, dim_date (year/quarter/month), dim_geography (region/country),
dim_product (category/subcategory), dim_customer (customer_segment).

Available years: 2022, 2023, 2024.
Regions: North America, Europe, Asia Pacific, Latin America.
Categories: Electronics, Furniture, Office Supplies, Clothing.
Customer segments: Consumer, Corporate, Home Office, Small Business.

When the user asks a question, call the most appropriate tool(s).
- For hierarchical navigation use drill_down / roll_up.
- For filtering use slice (one filter) or dice (multiple filters).
- For comparisons use compare_periods or yoy_growth.
- For rankings use top_n.
Always call at least one tool. If the question implies multiple steps, call multiple tools."""


def _dispatch(name: str, args: dict) -> dict[str, Any]:
    """Route a tool call name to the correct agent method."""
    if name == "drill_down":
        return _nav.drill_down(**args)
    if name == "roll_up":
        return _nav.roll_up(**args)
    if name == "slice":
        return _cube.slice(**args)
    if name == "dice":
        return _cube.dice(**args)
    if name == "pivot":
        return _cube.pivot(**args)
    if name == "yoy_growth":
        return _kpi.yoy_growth(**args)
    if name == "mom_change":
        return _kpi.mom_change(**args)
    if name == "profit_margins":
        return _kpi.profit_margins(**args)
    if name == "top_n":
        return _kpi.top_n(**args)
    if name == "compare_periods":
        return _kpi.compare_periods(**args)
    if name == "revenue_share":
        return _kpi.revenue_share(**args)
    return {"error": f"Unknown tool: {name}"}


def _keyword_fallback(query: str) -> list[dict[str, Any]]:
    """
    Simple keyword-based router used when no API key is configured.
    Handles the most common query patterns.
    """
    q = query.lower()
    results: list[dict[str, Any]] = []

    if "drill" in q and "down" in q:
        if "quarter" in q:
            results.append(_nav.drill_down("time", "year", "quarter"))
        elif "month" in q:
            results.append(_nav.drill_down("time", "quarter", "month"))
        elif "country" in q:
            results.append(_nav.drill_down("geography", "region", "country"))
        elif "subcategory" in q:
            results.append(_nav.drill_down("product", "category", "subcategory"))
        else:
            results.append(_nav.drill_down("time", "year", "quarter"))

    elif "roll" in q and "up" in q:
        results.append(_nav.roll_up("time", "month", "year"))

    elif "yoy" in q or "year-over-year" in q or "year over year" in q:
        group = None
        for dim in ["region", "category", "country", "subcategory", "customer_segment"]:
            if dim.replace("_", " ") in q or dim in q:
                group = dim
                break
        results.append(_kpi.yoy_growth(group_by=group))

    elif "mom" in q or "month-over-month" in q or "monthly trend" in q:
        year = None
        for y in [2022, 2023, 2024]:
            if str(y) in q:
                year = y
                break
        results.append(_kpi.mom_change(year=year))

    elif "top" in q or "best" in q or "ranking" in q or "highest" in q:
        measure = "revenue"
        for m in ["profit", "quantity"]:
            if m in q:
                measure = m
                break
        group = "country"
        for dim in ["region", "category", "subcategory", "customer_segment"]:
            if dim.replace("_", " ") in q or dim in q:
                group = dim
                break
        results.append(_kpi.top_n(measure=measure, n=5, group_by=group))

    elif "margin" in q or "profit margin" in q:
        group = "category"
        for dim in ["region", "subcategory", "customer_segment", "country"]:
            if dim.replace("_", " ") in q or dim in q:
                group = dim
                break
        results.append(_kpi.profit_margins(group_by=group))

    elif "compare" in q or "vs" in q:
        results.append(_kpi.compare_periods(
            period_a={"year": 2023},
            period_b={"year": 2024},
        ))

    elif "share" in q or "percentage" in q or "breakdown" in q:
        group = "region"
        for dim in ["category", "country", "customer_segment"]:
            if dim.replace("_", " ") in q or dim in q:
                group = dim
                break
        results.append(_kpi.revenue_share(group_by=group))

    elif "pivot" in q:
        results.append(_cube.pivot(rows="region", columns="year", values="revenue"))

    elif any(word in q for word in ["slice", "filter", "show only", "only"]):
        filters = {}
        for y in [2022, 2023, 2024]:
            if str(y) in q:
                filters["year"] = y
        for region in ["north america", "europe", "asia pacific", "latin america"]:
            if region in q:
                filters["region"] = region.title()
        for cat in ["electronics", "furniture", "office supplies", "clothing"]:
            if cat in q:
                filters["category"] = cat.title()
        if filters:
            results.append(_cube.dice(filters=filters))
        else:
            results.append(_cube.slice("year", 2024))

    else:
        results.append(_kpi.top_n(measure="revenue", n=5, group_by="region"))
        results.append(_kpi.yoy_growth())

    return results


class PlannerAgent:
    """
    Orchestrates the multi-agent BI pipeline using Hugging Face (Qwen 2.5).
    """

    def __init__(self) -> None:
        self._hf_client = None
        self._provider = None
        self._model = "Qwen/Qwen2.5-7B-Instruct"
        
        hf_token = (os.getenv("HUGGINGFACE_TOKEN") or "").strip()

        if hf_token:
            try:
                from huggingface_hub import InferenceClient
                self._hf_client = InferenceClient(model=self._model, token=hf_token)
                self._provider = "huggingface"
                logger.info(f"Hugging Face LLM enabled ({self._model})")
            except Exception as e:
                logger.warning("Hugging Face initialization failed: %s", e)

        if not self._provider:
            logger.info("LLM disabled: HUGGINGFACE_TOKEN not found in backend/.env")

    def _run_llm(self, query: str, history=None) -> list:
        """Use Hugging Face Inference API for tool calling."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in (history or []):
            messages.append(h)
        messages.append({"role": "user", "content": query})

        # HF Inference Client supports tool use for Qwen 2.5
        response = self._hf_client.chat_completion(
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=500,
        )

        message = response.choices[0].message
        if not message.tool_calls:
            return [{"operation": "message", "text": message.content or "No result.", "rows": []}]

        results: list[dict[str, Any]] = []
        for tc in message.tool_calls:
            name = tc.function.name
            args = tc.function.arguments if isinstance(tc.function.arguments, dict) else json.loads(tc.function.arguments)
            result = _dispatch(name, args)
            result["_tool"] = name
            result["_args"] = args
            results.append(result)
        return results

    def query(
        self,
        user_query: str,
        history=None,
        include_report: bool = True,
    ) -> dict:
        """Process a natural language BI query end-to-end."""
        using_llm = self._provider is not None
        llm_fallback_reason: str | None = None
        try:
            if using_llm:
                agent_results = self._run_llm(user_query, history)
            else:
                agent_results = _keyword_fallback(user_query)
        except Exception as exc:
            logger.warning("LLM call failed, falling back to keyword routing: %s", exc, exc_info=True)
            agent_results = _keyword_fallback(user_query)
            using_llm = False
            llm_fallback_reason = f"Hugging Face error: {exc!s}"

        reports: list[dict] = []
        summaries: list[dict] = []
        for res in agent_results:
            if res.get("error"):
                continue
            if include_report:
                try:
                    report = _rpt.generate_table(res)
                    reports.append(report)
                except Exception:
                    reports.append({"title": "Report error", "columns": [], "rows": [], "row_count": 0})
                try:
                    summary = _rpt.executive_summary(res)
                    summaries.append(summary)
                except Exception:
                    summaries.append({"summary": "Summary unavailable.", "highlights": [], "recommendations": []})

        combined_summary = " | ".join(s["summary"] for s in summaries if s.get("summary"))
        all_highlights = [h for s in summaries for h in s.get("highlights", [])]
        all_recommendations = [r for s in summaries for r in s.get("recommendations", [])]

        return {
            "query": user_query,
            "results": agent_results,
            "reports": reports,
            "summary": {
                "text": combined_summary,
                "highlights": all_highlights,
                "recommendations": all_recommendations,
            },
            "llm_used": using_llm,
            "provider": self._provider if using_llm else None,
            "llm_fallback_reason": llm_fallback_reason,
        }
