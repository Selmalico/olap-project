import json
import re
from agents.base_agent import BaseAgent
from tools.duckdb_executor import execute_query


class KPICalculatorAgent(BaseAgent):
    name = "kpi_calculator"
    description = "Calculates YoY, MoM, profit margins, rankings, Top-N"

    SYSTEM = """You are a KPI Calculator for business intelligence.

Calculations you can perform:
- YoY growth: use LAG(SUM(revenue)) OVER (PARTITION BY region ORDER BY year)
- MoM change: use LAG(SUM(revenue)) OVER (PARTITION BY ... ORDER BY year, month)
- Profit margin: profit / revenue * 100
- Top-N: ORDER BY metric DESC LIMIT N
- Rankings: RANK() OVER (ORDER BY SUM(revenue) DESC)

Use CTEs (WITH clauses) for complex multi-step calculations.
CRITICAL: Always use FROM read_parquet('{s3_path}') AS f

Return ONLY valid JSON:
{
  "sql": "WITH base AS (...) SELECT ...",
  "kpi_type": "yoy|mom|margin|top_n|ranking|mixed",
  "metrics": ["revenue_growth", "profit_margin"]
}"""

    def run(self, query: str, params: dict) -> dict:
        schema = self.schema_context()
        s3_path = schema.split("read_parquet('")[1].split("')")[0]
        system = self.SYSTEM.replace("{s3_path}", s3_path)
        msg = f"User query: {query}\nParameters: {json.dumps(params)}\nSchema:\n{schema}"
        response = self.call_llm(system, [{"role": "user", "content": msg}])
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if not match:
            raise ValueError(f"Agent returned no JSON: {response}")
        parsed = json.loads(match.group())
        data = execute_query(parsed["sql"])
        return {
            "sql": parsed["sql"],
            "data": data,
            "kpi_type": parsed.get("kpi_type"),
            "metrics": parsed.get("metrics", [])
        }
