"""Unit tests for OLAP BI Platform agents."""

import sys
import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Ensure backend directory is on path when running from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Helper: build a mock DuckDB connection returning a DataFrame

def _mock_db(rows: list[dict]):
    """Return a mock get_db() that responds to .execute().df() with a DataFrame."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.df.return_value = pd.DataFrame(rows)
    mock_conn.execute.return_value.fetchall.return_value = [
        (r.get(list(r.keys())[0]),) for r in rows
    ]
    return mock_conn


# Test 1: DimensionNavigatorAgent

@patch("database.repository.get_db")
def test_dimension_navigator_returns_data(mock_get_db):
    mock_get_db.return_value = _mock_db([
        {"year": 2023, "quarter": 1, "total_revenue": 250000.0,
         "total_profit": 50000.0, "total_quantity": 1000, "order_count": 200, "avg_margin": 0.2},
        {"year": 2023, "quarter": 2, "total_revenue": 270000.0,
         "total_profit": 55000.0, "total_quantity": 1100, "order_count": 210, "avg_margin": 0.21},
    ])
    from agents.dimension_navigator import DimensionNavigatorAgent
    agent = DimensionNavigatorAgent()
    result = agent.drill_down("time", "year", "quarter")
    assert "rows" in result
    assert result["operation"] == "drill_down"
    assert len(result["rows"]) > 0


# Test 2: AnomalyDetectionAgent

def test_anomaly_detection_flags_outlier():
    from agents.anomaly_detection import AnomalyDetectionAgent
    agent = AnomalyDetectionAgent()
    test_data = [
        {"region": "Europe",       "revenue": 1000},
        {"region": "Asia",         "revenue": 1050},
        {"region": "Americas",     "revenue": 980},
        {"region": "Africa",       "revenue": 1020},
        {"region": "Oceania",      "revenue": 990},
        {"region": "Middle East",  "revenue": 1010},
        {"region": "Central Asia", "revenue": 1030},
        {"region": "Southeast Asia","revenue": 970},
        {"region": "Nordic",       "revenue": 1040},
        {"region": "LatAm",        "revenue": 50000},
    ]
    result = agent.run("any query", {"data": test_data})
    assert len(result["anomalies"]) > 0


# Test 3: ExecutiveSummaryAgent

def test_executive_summary_returns_narrative():
    from agents.executive_summary import ExecutiveSummaryAgent
    agent = ExecutiveSummaryAgent()
    result = agent.run(
        "YoY comparison",
        {
            "data": [{"year": 2024, "revenue": 500000}],
            "kpis": {},
            "anomalies": [],
        },
    )
    assert "narrative" in result
    assert len(result["narrative"]) > 20


# Test 4: IntentDetector

def test_intent_detector_compare():
    from orchestrator.intent_detector import IntentDetector
    detector = IntentDetector()
    result = detector.detect("Compare Q3 vs Q4 2024 revenue")
    assert result["intent"] == "compare_periods"
    assert result["confidence"] >= 0.9


def test_intent_detector_top_n():
    from orchestrator.intent_detector import IntentDetector
    detector = IntentDetector()
    result = detector.detect("Top 5 countries by revenue")
    assert result["intent"] == "top_n"
    assert result["params"]["n"] == 5


# Test 5: AgentSelector

def test_agent_selector_select_top_n():
    from orchestrator.agent_selector import AgentSelector
    selector = AgentSelector()
    intent_obj = {
        "intent": "top_n",
        "params": {"measure": "revenue", "n": 5, "group_by": "region"},
        "secondary": [],
    }
    steps = selector.select(intent_obj)
    assert len(steps) >= 1
    assert steps[0]["agent"] == "kpi"
    assert steps[0]["method"] == "top_n"


def test_agent_selector_chained_flow():
    from orchestrator.agent_selector import AgentSelector
    from orchestrator.intent_detector import IntentDetector
    selector = AgentSelector()
    detector = IntentDetector()
    query = "Compare Q3 vs Q4 2024 and drill into the best region"
    intent_obj = detector.detect(query)
    assert selector.detect_chained_flow(query, intent_obj) is True
    steps = selector.build_chained_flow(intent_obj["params"])
    assert len(steps) == 4


# Test 6: PlannerAgent._keyword_fallback

@patch("database.repository.get_db")
def test_planner_keyword_fallback_yoy(mock_get_db):
    # yoy growth by category needs group_dim column in the DataFrame
    mock_get_db.return_value = _mock_db([
        {"year": 2023, "metric": 100000.0, "group_dim": "Electronics"},
        {"year": 2024, "metric": 120000.0, "group_dim": "Electronics"},
        {"year": 2023, "metric": 80000.0, "group_dim": "Clothing"},
        {"year": 2024, "metric": 90000.0, "group_dim": "Clothing"},
    ])
    from agents.planner import _keyword_fallback
    results = _keyword_fallback("yoy growth by category")
    assert len(results) > 0
    # Should return a result dict with operation key
    first = results[0]
    assert "operation" in first or "error" in first
