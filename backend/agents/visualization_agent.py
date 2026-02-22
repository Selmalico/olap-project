import json
import re
from agents.base_agent import BaseAgent


class VisualizationAgent(BaseAgent):
    name = "visualization_agent"
    description = "Recommends chart type and returns Recharts-compatible config"

    SYSTEM = """You are a Data Visualization expert specializing in business charts.

Chart selection rules:
- Time series data (year, month, quarter columns) -> LineChart
- Category comparisons (region, product, segment) -> BarChart
- Part-of-whole percentages -> PieChart
- Two different metrics on same axis -> ComposedChart (bar + line)
- Rankings or sorted values -> BarChart (horizontal if many categories)

Color palette: Use ["#2E75B6", "#00B0F0", "#1F7A4D", "#C55A11", "#5B2D8E", "#C00000"]

Return ONLY valid JSON:
{
  "chart_type": "LineChart|BarChart|PieChart|ComposedChart",
  "x_axis": "field_name_for_x_axis",
  "y_axes": [
    {"field": "revenue", "color": "#2E75B6", "type": "bar", "label": "Revenue"},
    {"field": "profit", "color": "#1F7A4D", "type": "line", "label": "Profit"}
  ],
  "title": "Chart title",
  "show_legend": true,
  "show_grid": true,
  "layout": "vertical|horizontal"
}"""

    def run(self, query: str, params: dict) -> dict:
        data = params.get("data", [])
        columns = list(data[0].keys()) if data else []
        msg = (
            f"User query: {query}\n"
            f"Available columns: {columns}\n"
            f"Row count: {len(data)}\n"
            f"Sample row: {json.dumps(data[0]) if data else '{}'}"
        )
        response = self.call_llm(self.SYSTEM, [{"role": "user", "content": msg}])
        match = re.search(r'\{.*\}', response, re.DOTALL)
        parsed = json.loads(match.group()) if match else {}
        return {"chart_config": parsed}
