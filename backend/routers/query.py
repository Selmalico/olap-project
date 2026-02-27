"""Natural language query endpoint – routes through the Planner agent."""

from __future__ import annotations

import json
import traceback
from typing import Any, List, Optional

from agents.anomaly_detection import AnomalyDetectionAgent
from agents.executive_summary import ExecutiveSummaryAgent
from agents.planner import PlannerAgent
from agents.report_generator import ReportGeneratorAgent
from agents.visualization_agent import VisualizationAgent
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from orchestrator.context_manager import add_turn, get_history, new_conversation_id
from orchestrator.intent_detector import IntentDetector
from pydantic import BaseModel
from utils import sanitize

try:
    from tools.supabase_log import log_query as _log_query
except ImportError:

    def _log_query(_: str) -> None:
        pass


router = APIRouter(prefix="/api/query", tags=["Natural Language Query"])
_planner = PlannerAgent()
_rpt = ReportGeneratorAgent()
_anomaly = AnomalyDetectionAgent()
_exec_summary = ExecutiveSummaryAgent()
_viz = VisualizationAgent()
_intent_detector = IntentDetector()
# In-memory store for last top dimension value per conversation
_context_store: dict = {}


@router.get("/llm-status")
async def llm_status() -> dict:
    """Check if an LLM provider is enabled (Gemini or OpenAI)."""
    return {
        "llm_enabled": _planner._provider is not None,
        "provider": _planner._provider,
    }


class QueryRequest(BaseModel):
    query: str
    history: Optional[List[dict]] = None
    conversation_id: Optional[str] = None


class DashboardRequest(BaseModel):
    pass


def _json_response(data: Any) -> Response:
    """Return JSON response; encode manually so numpy/serialization never causes 500."""
    try:
        clean = sanitize(data)
        body = json.dumps(clean, default=str)
        return Response(content=body, media_type="application/json", status_code=200)
    except (TypeError, ValueError) as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Response serialization failed.", "error": str(e)},
        )


@router.post(
    "/",
    responses={
        200: {
            "description": "Success. Returns query, results, reports, summary (text, highlights, recommendations), conversation_id."
        },
        500: {
            "description": "Server error (query processing or serialization failed)."
        },
    },
)
async def natural_language_query(body: QueryRequest) -> Response:
    """
    Process a natural language BI question.

    The Planner routes the query through specialist agents and returns
    formatted results, a report table, and an executive summary.
    """
    try:
        # Manage conversation ID and history
        conv_id = body.conversation_id or new_conversation_id()
        history = get_history(conv_id)

        # Resolve follow-up context before calling planner
        augmented_query = body.query
        intent_obj = _intent_detector.detect(body.query, history)
        if intent_obj.get("is_followup") and "region" in intent_obj.get(
            "context_refs", []
        ):
            ctx = _context_store.get(conv_id, {})
            last_top = ctx.get("last_top")
            if last_top:
                augmented_query = f"{body.query} (region: {last_top})"

        data = _planner.query(augmented_query, history=history)

        # Enrich results with anomaly detection, visualization, and executive summaries
        results = data.get("results", [])
        for result in results:
            rows = result.get("rows", [])

            # Add anomaly detection
            try:
                anomalies_info = _anomaly.detect(rows)
                result["anomalies"] = anomalies_info.get("anomalies", [])
                result["flagged_rows"] = anomalies_info.get("flagged_rows", [])
            except Exception:
                result["anomalies"] = []

            # Add visualization recommendation
            try:
                viz_config = _viz.recommend(result)
                result["chart_config"] = viz_config
            except Exception:
                pass

            # Add executive summary narrative
            try:
                summary_data = _exec_summary.summarize(result)
                result["executive_summary"] = summary_data.get("narrative", "")
            except Exception:
                pass

        # Save conversation turns
        summary_text = data.get("summary", {}).get("text", "")
        add_turn(conv_id, "user", body.query)
        add_turn(conv_id, "assistant", summary_text or "Analysis complete.")

        # Store top dimension value for follow-up context
        if results:
            first_result = results[0]
            rows = first_result.get("rows", [])
            if rows and isinstance(rows[0], dict) and "group_dim" in rows[0]:
                _context_store[conv_id] = {"last_top": rows[0]["group_dim"]}

        data["conversation_id"] = conv_id
        try:
            _log_query(body.query)
        except Exception:
            pass
        return _json_response(data)
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Query processing failed.",
                "error": str(e),
                "traceback": tb if __debug__ else None,
            },
        )


@router.get("/dashboard")
async def dashboard_cards() -> Response:
    """Return aggregated KPI cards for the main dashboard."""
    try:
        cards = _rpt.dashboard_cards()
        return _json_response({"cards": cards})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Dashboard data failed.", "error": str(e)},
        )


@router.get("/suggestions")
async def query_suggestions() -> dict[str, Any]:
    """Return example queries to guide the user."""
    return {
        "suggestions": [
            "What is total revenue by region for 2024?",
            "Show YoY growth by category",
            "Top 5 countries by profit",
            "Drill down from year to quarter",
            "Compare Q3 vs Q4 2024 revenue",
            "What is the profit margin by category?",
            "Show monthly revenue trend for 2024",
            "Pivot revenue by region and year",
            "Which customer segment generates the most revenue?",
            "Show revenue share by region",
        ]
    }
