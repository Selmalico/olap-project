import pytest
from unittest.mock import patch, MagicMock


def make_mock_client(json_text: str):
    mock = MagicMock()
    mock.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json_text)]
    )
    return mock


@patch('agents.base_agent.client')
def test_dimension_navigator_returns_data(mock_client):
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='{"sql": "SELECT year FROM parquet", "level": "year", "dimension": "time", "operation": "roll_up"}')]
    )
    from agents.dimension_navigator import DimensionNavigatorAgent
    with patch('agents.dimension_navigator.execute_query', return_value=[{"year": 2024, "revenue": 100000}]):
        agent = DimensionNavigatorAgent()
        result = agent.run("Revenue by year", {})
        assert "data" in result
        assert result["level"] == "year"
        assert len(result["data"]) > 0


@patch('agents.base_agent.client')
def test_anomaly_detection_flags_outlier(mock_client):
    from agents.anomaly_detection import AnomalyDetectionAgent
    agent = AnomalyDetectionAgent()
    test_data = [
        {"region": "Europe", "revenue": 1000},
        {"region": "Asia", "revenue": 1050},
        {"region": "Americas", "revenue": 980},
        {"region": "Africa", "revenue": 1020},
        {"region": "Oceania", "revenue": 990},
        {"region": "Middle East", "revenue": 1010},
        {"region": "Central Asia", "revenue": 1030},
        {"region": "Southeast Asia", "revenue": 970},
        {"region": "Nordic", "revenue": 1040},
        {"region": "LatAm", "revenue": 50000},  # Extreme outlier
    ]
    result = agent.run("any query", {"data": test_data})
    assert len(result["anomalies"]) > 0


@patch('agents.base_agent.client')
def test_executive_summary_returns_narrative(mock_client):
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Revenue grew 12% YoY. North America led growth at 18%. Recommend focus on APAC expansion.")]
    )
    from agents.executive_summary import ExecutiveSummaryAgent
    agent = ExecutiveSummaryAgent()
    result = agent.run("YoY comparison", {"data": [{"year": 2024, "revenue": 500000}], "kpis": {}, "anomalies": []})
    assert "narrative" in result
    assert len(result["narrative"]) > 20
