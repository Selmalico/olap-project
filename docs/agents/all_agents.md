# OLAP BI Platform - Agent Specifications

## Overview

The platform uses 7 specialized AI agents coordinated by a Planner/Orchestrator. Each agent is a Python class with specific methods that generate and execute SQL against the DuckDB data warehouse.

---

## Agent 1: Dimension Navigator

**Purpose**: Handles hierarchical OLAP operations and granular data access.

**Hierarchies**:
- **Time**: year → quarter → month
- **Geography**: region → country
- **Product**: category → subcategory

**Methods**:
- `drill_down(hierarchy, from_level, to_level=None, filters=None)`: Navigates to a finer level of granularity.
- `roll_up(hierarchy, from_level, to_level=None, filters=None)`: Navigates to a coarser level of granularity.
- `drill_through(filters=None, limit=100)`: Accesses raw fact table records (individual transactions).

**Example Result (drill_through)**: Returns individual `fact_sales` records with `order_id`, dimensions, and all measures.

---

## Agent 2: Cube Operations

**Purpose**: Handles fundamental OLAP cube manipulations: slice, dice, and pivot.

**Methods**:
- `slice(dimension, value, group_by=None, measures=None)`: Filters the cube on a single dimension value.
- `dice(filters, group_by=None, measures=None)`: Filters on multiple dimensions simultaneously.
- `pivot(rows, columns, values="revenue", filters=None, top_n=None)`: Reorganizes data into a cross-tabulation (rows × columns).
- `get_dimension_values(dimension)`: Returns all distinct values for a given dimension.

---

## Agent 3: KPI Calculator

**Purpose**: Calculates complex business KPIs and time-intelligence metrics.

**Methods**:
- `aggregate(measures=None, functions=None, group_by=None, filters=None)`: Flexible aggregation (SUM, AVG, COUNT).
- `yoy_growth(measure="revenue", group_by=None, filters=None)`: Year-over-Year growth analysis.
- `mom_change(measure="revenue", year=None, filters=None)`: Month-over-Month trend analysis.
- `top_n(measure="revenue", n=5, group_by="country", filters=None, ascending=False)`: Ranking analysis.
- `profit_margins(group_by="category", filters=None, sort_desc=True)`: Margin analysis by dimension.
- `revenue_share(group_by="region", filters=None)`: Percentage share of total.
- `ytd_revenue(year=2024, measure="revenue", group_by=None)`: Year-to-date cumulative metrics.
- `rolling_avg(measure="revenue", window=3, filters=None)`: Rolling moving averages.
- `compare_periods(period_a, period_b, measure="revenue", group_by=None)`: Arbitrary period comparison.

---

## Agent 4: Report Generator

**Purpose**: Formats raw data into structured report objects for the UI.

**Methods**:
- `generate_table(result, add_totals=True)`: Creates a titled report with typed columns and totals.
- `executive_summary(result)`: Generates a structured summary with highlights and recommendations.
- `dashboard_cards()`: Generates aggregated KPI cards for the main dashboard.

---

## Agent 5: Visualization Agent

**Purpose**: Recommends optimal chart types and Recharts configurations based on data structure.

**Chart Selection Logic**:
- Time series (year/month/quarter) → `LineChart`
- Category comparisons → `BarChart`
- Part-of-whole (share/margin) → `PieChart`
- Multiple metrics → `ComposedChart`

**Output**: Returns a `chart_config` object containing `chart_type`, axis mappings, and color palettes.

---

## Agent 6: Anomaly Detection

**Purpose**: Detects statistical outliers in results using Z-score analysis.

**Method**: Identifies values with a Z-score > 2.5 across numeric columns (revenue, profit, etc.).

**Note**: This agent performs local statistical analysis on the data returned by other agents; it does not generate SQL.

---

## Agent 7: Executive Summary

**Purpose**: Generates a natural language narrative (3-sentence summary) from analysis results.

**Method**: Uses the LLM to synthesize data rows, anomalies, and KPIs into a professional business narrative.

---

## Planner / Orchestrator

**Purpose**: Routes user queries to the appropriate agent(s) and method(s).

**Core Logic**:
1. **Intent Detection**: Identifies the operation (e.g., "drill down", "yoy") and extracts entities (dimensions, dates, measures).
2. **LLM Function Calling**: Uses **Hugging Face (Qwen 2.5)** to map natural language to specific agent method calls.
3. **Fallback Routing**: Uses a keyword-based `AgentSelector` if the LLM provider is unavailable.
4. **Enrichment**: Automatically chains the `ReportGenerator`, `VisualizationAgent`, `AnomalyDetection`, and `ExecutiveSummary` agents to every result.

**Output**: Returns a unified response containing the original query, agent execution results, formatted reports, charts, and a narrative summary.
