import json
import re
from agents.base_agent import BaseAgent
from tools.duckdb_executor import execute_query


class DimensionNavigatorAgent(BaseAgent):
    name = "dimension_navigator"
    description = "Handles drill-down and roll-up operations across dimensional hierarchies"

    SYSTEM = """You are an OLAP Dimension Navigator expert.

Hierarchies available:
- Time: year -> quarter -> month -> week
- Geography: region -> country
- Product: category -> subcategory

Given a user query, generate DuckDB SQL that navigates the appropriate hierarchy.
For drill-down: go one level deeper with GROUP BY at that level.
For roll-up: aggregate up to a higher level.

CRITICAL: Always use FROM read_parquet('{s3_path}') AS f
Use SUM(revenue), SUM(profit), SUM(quantity), AVG(profit_margin) as standard aggregates.

Return ONLY valid JSON in this exact format:
{
  "sql": "SELECT ... FROM read_parquet('...') AS f ...",
  "level": "year|quarter|month|week|region|country|category|subcategory",
  "dimension": "time|geography|product",
  "operation": "drill_down|roll_up"
}"""

    def run(self, query: str, params: dict) -> dict:
        schema = self.schema_context()
        s3_path = schema.split("read_parquet('")[1].split("')")[0]
        system = self.SYSTEM.replace("{s3_path}", s3_path)
        msg = f"User query: {query}\nParameters: {json.dumps(params)}\nSchema info:\n{schema}"
        response = self.call_llm(system, [{"role": "user", "content": msg}])
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if not match:
            raise ValueError(f"Agent returned no JSON: {response}")
        parsed = json.loads(match.group())
        data = execute_query(parsed["sql"])
        return {
            "sql": parsed["sql"],
            "data": data,
            "level": parsed.get("level"),
            "dimension": parsed.get("dimension"),
            "operation": parsed.get("operation")
        }
