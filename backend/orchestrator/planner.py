import json
import re
import uuid
from anthropic import Anthropic
from config import settings
from agents.dimension_navigator import DimensionNavigatorAgent
from agents.cube_operations import CubeOperationsAgent
from agents.kpi_calculator import KPICalculatorAgent
from agents.report_generator import ReportGeneratorAgent
from agents.visualization_agent import VisualizationAgent
from agents.anomaly_detection import AnomalyDetectionAgent
from agents.executive_summary import ExecutiveSummaryAgent
from orchestrator.context_manager import add_turn

client = Anthropic(api_key=settings.anthropic_api_key)

AGENTS = {
    "dimension_navigator": DimensionNavigatorAgent(),
    "cube_operations": CubeOperationsAgent(),
    "kpi_calculator": KPICalculatorAgent(),
    "report_generator": ReportGeneratorAgent(),
    "visualization_agent": VisualizationAgent(),
    "anomaly_detection": AnomalyDetectionAgent(),
    "executive_summary": ExecutiveSummaryAgent(),
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


def plan_and_execute(query: str, history: list, conversation_id: str = None) -> dict:
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # Step 1: Get routing plan
    plan_msg = f"User query: {query}\nConversation turns so far: {len(history)}"
    plan_response = client.messages.create(
        model=settings.model,
        max_tokens=1000,
        system=PLANNER_SYSTEM,
        messages=[{"role": "user", "content": plan_msg}]
    )
    plan_text = plan_response.content[0].text
    match = re.search(r'\{.*\}', plan_text, re.DOTALL)
    if not match:
        raise ValueError(f"Planner returned no JSON: {plan_text}")
    plan = json.loads(match.group())

    # Step 2: Execute agents in sequence
    results = []
    accumulated_data = []
    agent_names_used = []
    accumulated_anomalies = []

    for agent_name in plan.get("agents", []):
        if agent_name not in AGENTS:
            continue
        agent = AGENTS[agent_name]
        params = {
            **plan.get("parameters", {}),
            "data": accumulated_data,
            "anomalies": accumulated_anomalies,
            "kpis": {}
        }
        try:
            result = agent.run(query, params)
            # Accumulate data for downstream agents
            if result.get("data"):
                accumulated_data = result["data"]
            if result.get("anomalies"):
                accumulated_anomalies = result["anomalies"]
            results.append({"agent_name": agent_name, **result})
            agent_names_used.append(agent_name)
        except Exception as e:
            results.append({"agent_name": agent_name, "error": str(e), "data": None})

    # Step 3: Ensure executive summary runs with full context
    if "executive_summary" not in agent_names_used and accumulated_data:
        try:
            summary_result = AGENTS["executive_summary"].run(
                query,
                {"data": accumulated_data, "kpis": {}, "anomalies": accumulated_anomalies}
            )
            results.append({"agent_name": "executive_summary", **summary_result})
            agent_names_used.append("executive_summary")
        except Exception as e:
            pass

    exec_summary = next(
        (r.get("narrative") for r in results if r.get("agent_name") == "executive_summary"),
        None
    )

    # Step 4: Store in conversation history
    add_turn(conversation_id, "user", query)
    add_turn(conversation_id, "assistant", exec_summary or "Analysis complete.")

    return {
        "conversation_id": conversation_id,
        "agents_used": agent_names_used,
        "results": results,
        "executive_summary": exec_summary,
        "follow_up_questions": plan.get("follow_up_questions", [])
    }
