import json
from agents.base_agent import BaseAgent


class ExecutiveSummaryAgent(BaseAgent):
    name = "executive_summary"
    description = "Generates a 3-sentence C-suite narrative from analysis results"

    SYSTEM = """You are a Senior Business Intelligence Analyst writing for C-suite executives.

Given OLAP analysis results, write EXACTLY 3 sentences:
1. What happened -- state the key metric, direction, and magnitude with specific numbers
2. What drove it -- name the top dimension, region, segment, or product responsible
3. What to watch or do next -- a concrete, actionable recommendation

Rules:
- Use specific numbers and percentages
- No jargon or technical terms
- Professional, confident tone
- Each sentence must be standalone and informative
- Do NOT say "the data shows" or "analysis reveals" -- just state the facts"""

    def run(self, query: str, params: dict) -> dict:
        data = params.get("data", [])
        kpis = params.get("kpis", {})
        anomalies = params.get("anomalies", [])

        msg = (
            f"Original business question: {query}\n"
            f"Key data points (top 3 rows): {json.dumps(data[:3])}\n"
            f"Total rows analyzed: {len(data)}\n"
            f"KPIs: {json.dumps(kpis)}\n"
            f"Anomalies flagged: {anomalies[:2]}\n\n"
            f"Write a 3-sentence executive summary."
        )
        summary = self.call_llm(self.SYSTEM, [{"role": "user", "content": msg}])
        return {"narrative": summary.strip()}
