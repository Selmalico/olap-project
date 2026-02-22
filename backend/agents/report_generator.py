import json
import re
from agents.base_agent import BaseAgent


class ReportGeneratorAgent(BaseAgent):
    name = "report_generator"
    description = "Formats analysis results into structured report objects"

    SYSTEM = """You are a Business Report Formatter.

Given raw OLAP query results, produce a structured report format.
Analyze the data and identify: column types, totals, key highlights.

Return ONLY valid JSON:
{
  "title": "Descriptive report title",
  "summary": "2-3 sentence plain English summary of what the data shows",
  "columns": [
    {"name": "column_name", "type": "number|string|percent|currency", "format": "optional format hint"}
  ],
  "totals_row": {"column_name": "total_value"},
  "highlights": [
    "Key insight 1 with specific number",
    "Key insight 2 with specific number"
  ]
}"""

    def run(self, query: str, params: dict) -> dict:
        data = params.get("data", [])
        sample = data[:5] if data else []
        msg = (
            f"Original query: {query}\n"
            f"Data sample (first 5 rows): {json.dumps(sample)}\n"
            f"Total rows in result: {len(data)}\n"
            f"All column names: {list(data[0].keys()) if data else []}"
        )
        response = self.call_llm(self.SYSTEM, [{"role": "user", "content": msg}])
        match = re.search(r'\{.*\}', response, re.DOTALL)
        parsed = json.loads(match.group()) if match else {}
        return {"formatted": parsed, "data": data}
