# OLAP BI Platform - Agent Specifications

## Overview

The platform uses 7 specialized AI agents coordinated by a Planner/Orchestrator. Each agent receives the user's query, accumulated parameters, and returns structured results.

---

## Agent 1: Dimension Navigator

**Purpose**: Handles drill-down and roll-up operations across dimensional hierarchies.

**Hierarchies**:
- Time: year -> quarter -> month -> week
- Geography: region -> country
- Product: category -> subcategory

**Input Parameters**:
```json
{
  "query": "string - user's natural language query",
  "params": {
    "drill_dimension": "time|geography|product",
    "drill_level": "year|quarter|month|week|region|country|category|subcategory"
  }
}
```

**Output Schema**:
```json
{
  "sql": "generated DuckDB SQL",
  "data": [{"column": "value"}],
  "level": "current hierarchy level",
  "dimension": "time|geography|product",
  "operation": "drill_down|roll_up"
}
```

**Example Query**: "Break down 2024 revenue by quarter"
**Expected Output**: 4 rows with quarter, revenue, profit, quantity aggregates

---

## Agent 2: Cube Operations

**Purpose**: Handles slice, dice, and pivot OLAP operations.

**Operations**:
- SLICE: Filter on a single dimension
- DICE: Filter on multiple dimensions
- PIVOT: Reorganize using conditional aggregation

**Input Parameters**:
```json
{
  "query": "string",
  "params": {
    "filters": {"year": 2024, "region": "Europe"}
  }
}
```

**Output Schema**:
```json
{
  "sql": "generated SQL with WHERE clauses",
  "data": [{"column": "value"}],
  "operation": "slice|dice|pivot",
  "filters_applied": ["year = 2024", "region = Europe"]
}
```

**Example Query**: "Show Electronics sales in Europe for 2024"
**Expected Output**: Filtered dataset with Electronics+Europe+2024 data

---

## Agent 3: KPI Calculator

**Purpose**: Calculates business KPIs including growth rates, rankings, and margins.

**Capabilities**:
- YoY growth using LAG window functions
- MoM change calculations
- Profit margin computation
- Top-N rankings
- RANK() window functions

**Input Parameters**:
```json
{
  "query": "string",
  "params": {
    "kpi_type": "yoy|mom|margin|top_n|ranking",
    "top_n": 5
  }
}
```

**Output Schema**:
```json
{
  "sql": "CTE-based SQL for complex calculations",
  "data": [{"column": "value"}],
  "kpi_type": "yoy|mom|margin|top_n|ranking|mixed",
  "metrics": ["revenue_growth", "profit_margin"]
}
```

**Example Query**: "Top 5 countries by profit margin"
**Expected Output**: 5 rows ranked by profit margin percentage

---

## Agent 4: Report Generator

**Purpose**: Formats raw OLAP results into structured report objects.

**Input Parameters**:
```json
{
  "query": "string",
  "params": {
    "data": [{"column": "value"}]
  }
}
```

**Output Schema**:
```json
{
  "formatted": {
    "title": "Report title",
    "summary": "Plain English summary",
    "columns": [{"name": "col", "type": "number|string|percent|currency"}],
    "totals_row": {"column": "total"},
    "highlights": ["Key insight with number"]
  },
  "data": [{"column": "value"}]
}
```

**Example**: Given revenue-by-region data, produces a titled report with currency-formatted columns and highlight insights.

---

## Agent 5: Visualization Agent

**Purpose**: Recommends optimal chart type and returns Recharts-compatible configuration.

**Chart Selection Rules**:
- Time series -> LineChart
- Category comparisons -> BarChart
- Part-of-whole -> PieChart
- Multiple metrics -> ComposedChart

**Input Parameters**:
```json
{
  "query": "string",
  "params": {
    "data": [{"column": "value"}]
  }
}
```

**Output Schema**:
```json
{
  "chart_config": {
    "chart_type": "LineChart|BarChart|PieChart|ComposedChart",
    "x_axis": "field_name",
    "y_axes": [
      {"field": "revenue", "color": "#2E75B6", "type": "bar", "label": "Revenue"}
    ],
    "title": "Chart title",
    "show_legend": true,
    "show_grid": true,
    "layout": "vertical|horizontal"
  }
}
```

**Color Palette**: `["#2E75B6", "#00B0F0", "#1F7A4D", "#C55A11", "#5B2D8E", "#C00000"]`

---

## Agent 6: Anomaly Detection

**Purpose**: Detects statistical outliers using Z-score analysis (no LLM calls).

**Method**: Z-score > 2.5 threshold on all numeric columns.

**Input Parameters**:
```json
{
  "query": "string",
  "params": {
    "data": [{"column": "value"}]
  }
}
```

**Output Schema**:
```json
{
  "anomalies": ["revenue for LatAm: 50,000.00 is 340.5% from mean (11,340.00)"],
  "flagged_rows": [5],
  "columns_analyzed": ["revenue", "profit", "quantity"]
}
```

**Note**: Caps output at 5 most notable anomalies. Requires minimum 4 data rows.

---

## Agent 7: Executive Summary

**Purpose**: Generates a 3-sentence C-suite narrative from analysis results.

**Structure**:
1. What happened (key metric + direction + magnitude)
2. What drove it (top dimension/region/product responsible)
3. What to watch or do next (actionable recommendation)

**Input Parameters**:
```json
{
  "query": "string",
  "params": {
    "data": [{"column": "value"}],
    "kpis": {},
    "anomalies": []
  }
}
```

**Output Schema**:
```json
{
  "narrative": "3-sentence executive summary with specific numbers"
}
```

**Example Output**: "Revenue grew 12% year-over-year to $5.2M in 2024. North America led growth at 18%, driven by Electronics category expansion. Recommend increasing inventory allocation to APAC where Q4 demand outpaced supply by 23%."

---

## Planner / Orchestrator

**Purpose**: Routes user queries to the appropriate agent sequence.

**Always included**: report_generator, visualization_agent, executive_summary

**Routing logic** (determined by Claude):
- Drill/roll-up keywords -> dimension_navigator
- Filter keywords -> cube_operations
- Growth/comparison keywords -> kpi_calculator
- Unusual/pattern keywords -> anomaly_detection

**Output**: Execution plan with agent sequence, parameters, and follow-up question suggestions.
