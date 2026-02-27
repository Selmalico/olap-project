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
from orchestrator.intent_detector import IntentDetector
from orchestrator.agent_selector import AgentSelector
from agents.visualization_agent import VisualizationAgent
from agents.anomaly_detection import AnomalyDetectionAgent
from agents.executive_summary import ExecutiveSummaryAgent

_cube = CubeOperationsAgent()
_nav = DimensionNavigatorAgent()
_kpi = KPICalculatorAgent()
_rpt = ReportGeneratorAgent()
_viz = VisualizationAgent()
_anomaly = AnomalyDetectionAgent()
_exec_summary = ExecutiveSummaryAgent()
_detector = IntentDetector()
_selector = AgentSelector()

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
    {
        "type": "function",
        "function": {
            "name": "ytd_revenue",
            "description": "Year-to-date (YTD) cumulative revenue for a given year. Shows running total by month.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "default": 2024},
                    "measure": {"type": "string", "default": "revenue"},
                    "group_by": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rolling_avg",
            "description": "Calculate a rolling N-month moving average for a measure (time intelligence).",
            "parameters": {
                "type": "object",
                "properties": {
                    "measure": {"type": "string", "default": "revenue"},
                    "window": {"type": "integer", "default": 3},
                    "filters": {"type": "object"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "drill_through",
            "description": "Drill through to raw transaction records from the fact table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filters": {"type": "object"},
                    "limit": {"type": "integer", "default": 50},
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
    if name == "ytd_revenue":
        return _kpi.ytd_revenue(**args)
    if name == "rolling_avg":
        return _kpi.rolling_avg(**args)
    if name == "aggregate":
        return _kpi.aggregate(**args)
    if name == "drill_through":
        return _nav.drill_through(**args)
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

    elif "ytd" in q or "year to date" in q or "year-to-date" in q or "cumulative" in q:
        years = [y for y in [2022, 2023, 2024] if str(y) in q]
        year = years[0] if years else 2024
        measure = "revenue"
        for m in ["profit", "quantity", "cost"]:
            if m in q:
                measure = m
                break
        results.append(_kpi.ytd_revenue(year=year, measure=measure))

    elif "rolling" in q or "moving average" in q:
        import re as _re2
        m2 = _re2.search(r"\b(\d+).?month", q, _re2.I)
        window = int(m2.group(1)) if m2 else 3
        results.append(_kpi.rolling_avg(window=window))

    elif any(word in q for word in ["drill through", "drill-through", "raw records", "raw data", "individual records", "detailed records", "show transactions"]):
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
        results.append(_nav.drill_through(filters=filters, limit=50))

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

    elif any(word in q for word in ["how many", "count", "number of", "transactions", "orders", "how much", "what is", "what are", "show", "total", "sum"]):
        # Build filters from query
        filters = {}
        for y in [2022, 2023, 2024]:
            if str(y) in q:
                filters["year"] = y
        import re as _re3
        qt = _re3.search(r"\bq([1-4])\b", q)
        if qt:
            filters["quarter"] = int(qt.group(1))
        for region in ["north america", "europe", "asia pacific", "latin america"]:
            if region in q:
                filters["region"] = region.title()
        for cat in ["electronics", "furniture", "office supplies", "clothing"]:
            if cat in q:
                filters["category"] = cat.title()
        for seg in ["consumer", "corporate", "home office", "small business"]:
            if seg in q:
                filters["customer_segment"] = seg.title()

        # Detect if it's a count/transaction query
        is_count = any(w in q for w in ["how many", "count", "number of", "transactions", "orders", "sales made"])
        # Detect grouping dimension
        group = None
        for dim in ["category", "subcategory", "country", "region", "customer_segment", "quarter", "month", "year"]:
            if dim.replace("_", " ") in q and dim not in filters:
                group = dim
                break
        measure = "revenue"
        for m in ["profit", "quantity", "cost", "profit_margin"]:
            if m.replace("_", " ") in q or m in q:
                measure = m
                break

        if is_count:
            # Use aggregate with COUNT
            results.append(_kpi.aggregate(
                measures=["revenue"],
                functions=["COUNT", "SUM"],
                group_by=group,
                filters=filters,
            ))
        elif group and group not in ("year", "quarter", "month"):
            results.append(_kpi.top_n(measure=measure, n=10, group_by=group, filters=filters))
        elif group in ("year", "quarter", "month"):
            results.append(_kpi.aggregate(measures=[measure], functions=["SUM"], group_by=group, filters=filters))
        else:
            results.append(_kpi.aggregate(measures=[measure], functions=["SUM", "COUNT"], filters=filters))

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
                import requests
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry

                # Configure retries for robust connection
                retry_strategy = Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["POST", "GET"]
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session = requests.Session()
                session.mount("https://", adapter)
                session.mount("http://", adapter)

                self._hf_client = InferenceClient(
                    model=self._model, 
                    token=hf_token,
                    headers={"X-Wait-For-Model": "true"}
                )
                # Note: Newer versions of huggingface_hub use httpx or allow passing a session
                # If using requests-based version:
                if hasattr(self._hf_client, "session"):
                    self._hf_client.session = session
                
                self._provider = "huggingface"
                logger.info(f"Hugging Face LLM enabled ({self._model})")
            except Exception as e:
                logger.warning("Hugging Face initialization failed: %s", e)

        if not self._provider:
            logger.info("LLM disabled: HUGGINGFACE_TOKEN not found in backend/.env")

    def _run_llm(self, query: str, history=None) -> list:
        """Use Hugging Face Inference API for tool calling with retries."""
        import time
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in (history or []):
            messages.append(h)
        messages.append({"role": "user", "content": query})

        max_retries = 3
        retry_delay = 1
        last_exception = None

        for attempt in range(max_retries):
            try:
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
            except Exception as e:
                last_exception = e
                # Only retry on connection-related errors
                err_str = str(e).lower()
                if any(msg in err_str for msg in ["connection", "timeout", "aborted", "reset", "10054"]):
                    logger.warning(f"HF attempt {attempt+1} failed: {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise e
        
        raise last_exception if last_exception else Exception("HF call failed after retries")

    def _execute_step(self, step: dict, last_result: dict | None) -> dict:
        """Execute a single AgentSelector step, returning its result."""
        agent_key = step["agent"]
        method_name = step["method"]
        params = dict(step.get("params", {}))

        # Resolve {BEST_<DIM>} placeholders from prior step result
        if last_result:
            rows = last_result.get("rows", [])
            winner = rows[0].get("group_dim") if rows else None
            if winner:
                for key, val in list(params.items()):
                    if isinstance(val, str) and val.startswith("{BEST_"):
                        params[key] = winner
                    elif isinstance(val, dict):
                        for k2, v2 in list(val.items()):
                            if isinstance(v2, str) and v2.startswith("{BEST_"):
                                val[k2] = winner

        agent_map = {"kpi": _kpi, "cube": _cube, "nav": _nav, "report": _rpt}
        agent = agent_map.get(agent_key)
        if agent is None:
            return {"error": f"Unknown agent"}
        method = getattr(agent, method_name, None)
        if method is None:
            return {"error": f"Agent has no method"}
        try:
            return method(**params)
        except Exception as exc:
            return {"error": str(exc)}

    def _run_orchestrated(self, user_query: str, history=None) -> list[dict]:
        """Use IntentDetector + AgentSelector to build and execute a step plan."""
        intent_obj = _detector.detect(user_query, history)

        if _selector.detect_chained_flow(user_query, intent_obj):
            steps = _selector.build_chained_flow(intent_obj["params"])
        else:
            steps = _selector.select(intent_obj)

        results: list[dict] = []
        last_result: dict | None = None
        for step in steps:
            result = self._execute_step(step, last_result)
            result["_step_label"] = step.get("label", "")
            result["_tool"] = f"{step['agent']}.{step['method']}"
            results.append(result)
            if not result.get("error"):
                last_result = result

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
                agent_results = self._run_orchestrated(user_query, history)
        except Exception as exc:
            logger.warning("LLM call failed, falling back to keyword routing: %s", exc, exc_info=True)
            agent_results = self._run_orchestrated(user_query, history)
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

        # Build agent names from results
        agents_used = []
        for res in agent_results:
            tool = res.get("_tool", "") or res.get("_step_label", "")
            if tool:
                agents_used.append(tool)
            else:
                op = res.get("operation", "")
                if op:
                    agents_used.append(op)

        # Generate follow-up questions based on operations performed
        follow_up_questions = self._generate_follow_ups(agent_results, user_query)

        return {
            "query": user_query,
            "results": agent_results,
            "reports": reports,
            "summary": {
                "text": combined_summary,
                "highlights": all_highlights,
                "recommendations": all_recommendations,
            },
            "agents_used": agents_used,
            "follow_up_questions": follow_up_questions,
            "llm_used": using_llm,
            "provider": self._provider if using_llm else None,
            "llm_fallback_reason": llm_fallback_reason,
        }

    def _generate_follow_ups(self, results: list[dict], query: str) -> list[str]:
        """Generate context-aware follow-up suggestions based on what was computed."""
        ops = [r.get("operation", r.get("_tool", "")) for r in results if not r.get("error")]
        q = query.lower()
        suggestions = []

        op_follow_ups = {
            "yoy_growth":      ["Show month-over-month trend for 2024", "Which category had the best YoY growth?", "Compare Q3 vs Q4 this year"],
            "mom_change":      ["Show YoY growth for the same metric", "Which region had the biggest monthly swing?", "Show YTD cumulative revenue for 2024"],
            "compare_periods": ["Show profit margins for each region", "Drill down into the best quarter", "Show YoY growth by category"],
            "top_n":           ["Show profit margins for these groups", "Compare with last year's rankings", "Drill into the top performer"],
            "profit_margins":  ["Show revenue for the same groups", "Which subcategory has the lowest margin?", "Compare margins YoY"],
            "revenue_share":   ["Show absolute revenue for each group", "Compare revenue share 2023 vs 2024", "Drill down to country level"],
            "drill_down":      ["Roll up to the higher level", "Show profit margins at this level", "Which sub-group has the highest profit?"],
            "roll_up":         ["Drill down for more detail", "Compare year-over-year at this level", "Show revenue share"],
            "drill_through":   ["Summarise these by category", "Show top 5 by revenue", "Filter to a specific region"],
            "slice":           ["Add more filters (dice operation)", "Show YoY growth for this slice", "Which sub-group performs best?"],
            "dice":            ["Show profit margins for this combination", "Drill down within this view", "Compare with a different period"],
            "pivot":           ["Show the same pivot for profit margin", "Which cell has the highest value?", "Compare this pivot with 2023"],
            "ytd_revenue":     ["Compare YTD vs same period last year", "Show month-over-month within this year", "Which category drives the most YTD revenue?"],
            "rolling_avg":     ["Show raw monthly data alongside this", "Which month had the biggest deviation from the trend?", "Extend to a 6-month rolling average"],
            "aggregate":       ["Break this down by category", "Break this down by region", "Show YoY growth for the same filters"],
        }

        for op in ops:
            if op in op_follow_ups and len(suggestions) < 3:
                for q_sug in op_follow_ups[op]:
                    if q_sug not in suggestions:
                        suggestions.append(q_sug)
                        if len(suggestions) >= 3:
                            break

        if not suggestions:
            suggestions = [
                "Show revenue breakdown by region",
                "Compare 2023 vs 2024 performance",
                "Which product category has the highest profit margin?",
            ]

        return suggestions[:3]
