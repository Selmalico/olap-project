import json
import re
from agents.base_agent import BaseAgent
from tools.duckdb_executor import execute_query


class CubeOperationsAgent(BaseAgent):
    name = "cube_operations"
    description = "Handles slice, dice, and pivot OLAP operations"

    SYSTEM = """You are an OLAP Cube Operations expert.

Operations:
- SLICE: Filter on a single dimension (e.g., WHERE year = 2024)
- DICE: Filter on multiple dimensions (e.g., WHERE year = 2024 AND region = 'Europe')
- PIVOT: Reorganize perspective using conditional aggregation

CRITICAL: Always use FROM read_parquet('{s3_path}') AS f

Return ONLY valid JSON:
{
  "sql": "SELECT ... FROM read_parquet('...') AS f WHERE ...",
  "operation": "slice|dice|pivot",
  "filters_applied": ["filter description 1", "filter description 2"]
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
            "operation": parsed.get("operation"),
            "filters_applied": parsed.get("filters_applied", [])
        }
