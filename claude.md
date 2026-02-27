# CLAUDE.md — Multi-Agent OLAP Business Intelligence Platform

---

## STUDENT PROMPT — PASTE THIS AT THE START OF EVERY AI SESSION

> This is the master prompt to give Claude Code (or any AI coding assistant) when starting or
> continuing work on this project. It establishes context, role, stack, requirements, and
> implementation order so the AI can act as a senior architect guiding a student.

```
You are helping me, a computer science student, complete my Tier 3: Architect capstone project.
I am building a production-grade Multi-Agent OLAP Business Intelligence Platform.
My goal is to achieve an A+ (Excellent, 90–100%) grade.

--- MY ROLE AS A STUDENT ---
I am a CS student with intermediate knowledge of Python, JavaScript, SQL, and REST APIs.
I need you to act as my senior software architect and pair programmer.
Guide me step by step, explaining every major design decision so I genuinely learn the
architecture patterns — not just copy code blindly.
When I ask "why", explain the architectural reasoning.
When I make a mistake, correct me and explain what went wrong.
Treat this as a real production project, not a toy example.
Do not skip steps or combine phases without telling me.

--- PROJECT OVERVIEW ---
I am building a modular, multi-agent Business Intelligence platform that lets users ask natural
language questions about global retail sales data and receive structured analytical results,
interactive charts, and executive summaries.

Think of it as a mini Tableau / Power BI with AI-powered agents instead of fixed queries.

System architecture:

  FRONTEND  (React + TypeScript + Vite + TailwindCSS + Recharts)
       |
  API LAYER  (FastAPI — Python)
       |
  PLANNER / ORCHESTRATOR  ← the "brain" that routes every query
       |
  ┌─────────┬─────────┬─────────┬─────────┐
  |         |         |         |         |
Agent 1  Agent 2  Agent 3  Agent 4  Agents 5-7
Dim Nav  Cube Ops  KPI Calc  Report   (Optional)
  |         |         |         |         |
  └─────────┴─────────┴─────────┴─────────┘
       |
  DATA ACCESS LAYER  (DuckDB reading Parquet files)
       |
  STAR SCHEMA  (fact_sales + dim_date + dim_geography + dim_product + dim_customer)

--- TECHNICAL STACK ---
Backend   : Python 3.11 + FastAPI + DuckDB (reads local Parquet or S3 Parquet)
LLM       : Anthropic Claude — model id: claude-sonnet-4-6
            Use the anthropic Python SDK: client.messages.create(...)
Frontend  : React + TypeScript + Vite + TailwindCSS + Recharts
Database  : DuckDB star schema  (no PostgreSQL needed — DuckDB is in-process)
Deployment: Render (backend) + Vercel (frontend)  OR  local dev for demo

--- THE FOUR REQUIRED AGENTS — must implement all four for a passing grade ---

AGENT 1: Dimension Navigator
  Purpose  : Navigate dimensional hierarchies in the star schema
  Drill-Down  : year → quarter → month → week  (finer granularity)
  Roll-Up     : week → month → quarter → year   (coarser granularity)
  Drill-Through: return raw transaction rows behind an aggregated number
  Input   : user query (str) + params dict  { drill_dimension, drill_level, filters }
  Output  : { sql, data, level, dimension, operation }

AGENT 2: Cube Operations
  Purpose  : Classic OLAP cube manipulations
  Slice  : filter on ONE dimension     e.g. WHERE year = 2024
  Dice   : filter on MULTIPLE dims     e.g. WHERE year=2024 AND region='Europe'
  Pivot  : reorganize perspective      e.g. regions as rows, months as columns
  Input   : user query + params dict  { filters: {}, operation_hint }
  Output  : { sql, data, operation, filters_applied }

AGENT 3: KPI Calculator
  Purpose  : Compute business metrics and period comparisons
  Capabilities:
    - YoY growth  using LAG() window functions
    - MoM change  using LAG() over month partitions
    - Profit margin  (profit / revenue * 100)
    - Top-N / Bottom-N  (ORDER BY metric DESC LIMIT N)
    - Period comparison between any two date ranges
  Use CTEs (WITH clauses) for multi-step calculations.
  Input   : user query + params dict  { kpi_type, top_n }
  Output  : { sql, data, kpi_type, metrics[] }

AGENT 4: Report Generator
  Purpose  : Format raw data rows into a structured report object
  Output schema:
    { title, summary, columns[{name, type, format}], totals_row{}, highlights[] }
  summary  = 2-3 plain-English sentences about what the data shows
  highlights = bullet points with specific numbers
  Input   : original user query + raw data rows from upstream agents
  Output  : { formatted: <report object>, data: <original rows> }

--- THREE OPTIONAL AGENTS — implement all three for A+ grade ---

AGENT 5: Visualization Agent
  Purpose: Choose the best Recharts chart type and return a render config
  Rules:
    time columns (year/month/quarter) → LineChart
    category comparisons (region/product) → BarChart
    part-of-whole percentages → PieChart
    two metrics on same chart → ComposedChart (bar + line)
  Output: { chart_type, x_axis, y_axes[{field, color, type, label}], title,
             show_legend, show_grid }
  Color palette: ["#2E75B6","#00B0F0","#1F7A4D","#C55A11","#5B2D8E","#C00000"]

AGENT 6: Anomaly Detection Agent
  Purpose: Flag statistical outliers — NO LLM call, pure pandas/numpy
  Method : Z-score with threshold = 2.5 on all numeric columns
  Output : { anomalies: ["human readable string"...], flagged_rows: [int...],
             columns_analyzed: [str...] }

AGENT 7: Executive Summary Agent
  Purpose: Write a 3-sentence C-suite narrative from the analysis results
  Sentence 1 — What happened: key metric + direction + magnitude + specific numbers
  Sentence 2 — What drove it: top dimension / region / product responsible
  Sentence 3 — What to do next: concrete, actionable recommendation
  Rules: use real numbers, no "the data shows" phrasing, professional tone
  Output : { narrative: "Three sentences here." }

--- THE PLANNER / ORCHESTRATOR ---
The planner is the central brain. Every user query goes through it.

Responsibilities:
  1. Call the LLM to produce a routing plan: which agents + order + parameters
  2. Execute agents sequentially, passing accumulated data downstream
  3. ALWAYS run: report_generator → visualization_agent → executive_summary
  4. Run anomaly_detection when query involves trends, comparisons, or anomalies
  5. Maintain a conversation context store (in-memory dict keyed by conversation_id)
  6. Return unified response:
     { conversation_id, agents_used[], results[], executive_summary, follow_up_questions[] }

Planner output JSON format:
  {
    "intent": "drill_down|roll_up|slice|dice|kpi|compare|aggregate|pivot",
    "agents": ["agent1", ..., "report_generator", "visualization_agent", "executive_summary"],
    "parameters": { "filters": {}, "drill_dimension": "", "kpi_type": "", "top_n": null },
    "follow_up_questions": ["Q1?", "Q2?", "Q3?"]
  }

--- DATABASE: STAR SCHEMA ---
Source: 10,000 rows of global retail sales 2022–2024 (generated synthetic data)
Source columns: order_id, order_date, year, quarter, month, month_name, week,
                region, country, category, subcategory, customer_segment,
                quantity, unit_price, revenue, cost, profit, profit_margin

Star schema tables (created in DuckDB from the Parquet file):
  fact_sales    — FK references + measures: quantity, unit_price, revenue, cost, profit, profit_margin
  dim_date      — date_key, year, quarter, month, month_name, week
  dim_geography — geo_key, region, country
  dim_product   — product_key, category, subcategory
  dim_customer  — customer_key, segment

All SQL agents use this FROM clause pattern:
  FROM read_parquet('data/parquet/fact_sales.parquet') AS f

--- FRONTEND COMPONENTS REQUIRED ---
  Chat page       : text input + message history (user bubbles + assistant cards)
  AgentTracker    : badge row showing which agents ran (animated spinner while loading)
  DataTable       : formatted table, numbers localised, "show all rows" expander
  ChartPanel      : renders Recharts chart from visualization_agent config JSON
  ExportToolbar   : "Export PDF" button + email input field + "Send" button
  Starter chips   : clickable example question buttons on empty state

Frontend API calls:
  POST /query       — main query endpoint
  POST /export/pdf  — generate and return presigned PDF download URL
  POST /email/send  — email the PDF report via SES
  GET  /schema      — fetch schema metadata for display

--- REQUIRED FILE STRUCTURE ---
olap-project/
  backend/
    main.py                     ← FastAPI entry point (4 endpoints)
    config.py                   ← pydantic-settings (reads .env)
    requirements.txt
    .env                        ← secrets (gitignored)
    agents/
      base_agent.py             ← abstract BaseAgent with call_llm() + schema_context()
      dimension_navigator.py
      cube_operations.py
      kpi_calculator.py
      report_generator.py
      visualization_agent.py
      anomaly_detection.py
      executive_summary.py
    orchestrator/
      planner.py                ← plan_and_execute() — the brain
      context_manager.py        ← in-memory conversation store
    tools/
      duckdb_executor.py        ← execute_query() + get_schema_info()
      pdf_generator.py          ← generate_pdf() using WeasyPrint + Jinja2
      email_sender.py           ← send_report_email() via AWS SES
      s3_client.py              ← upload_pdf_get_url() to S3
    models/
      schemas.py                ← Pydantic request/response models
    templates/
      report.html               ← Jinja2 HTML template for PDF
    tests/
      test_agents.py            ← pytest unit tests for each agent
  frontend/
    src/
      components/
        AgentTracker.tsx
        DataTable.tsx
        ChartPanel.tsx
        ExportToolbar.tsx
      hooks/
        useChat.ts
      pages/
        Chat.tsx
      services/
        api.ts
      App.tsx
  data/
    generate_dataset.py         ← creates 10k row CSV
    load_to_parquet.py          ← converts CSV → Parquet
    raw/                        ← gitignored
    parquet/                    ← gitignored
  database/
    schema.sql                  ← DuckDB star schema DDL

--- GRADING TARGET: EXCELLENT (90–100%) ---
To achieve top marks I need ALL of the following:
  - All 4 required agents + all 3 optional agents implemented and working
  - Planner routes complex multi-step queries correctly
  - Star schema properly implemented in DuckDB
  - React frontend with charts, agent tracker, and export toolbar
  - PDF export working (WeasyPrint + Jinja2 template)
  - Email delivery working (AWS SES)
  - Pytest tests for all agents
  - Architecture diagram, API docs, agent specs, user guide
  - Deployment working (Render + Vercel)

--- IMPLEMENTATION ORDER — follow this sequence exactly ---
  Phase 1 : Data generation — generate_dataset.py → CSV, load_to_parquet.py → Parquet
  Phase 2 : Backend core — config.py, models/schemas.py, tools/duckdb_executor.py, base_agent.py
  Phase 3 : All 7 agents — one file at a time, verify each before moving on
  Phase 4 : Orchestrator — context_manager.py then planner.py
  Phase 5 : FastAPI main.py — 4 endpoints, start uvicorn, verify /docs loads
  Phase 6 : PDF + Email tools — pdf_generator.py, email_sender.py, s3_client.py
  Phase 7 : React frontend — components → hooks → pages → api service
  Phase 8 : Tests — pytest for each agent in tests/test_agents.py
  Phase 9 : Deployment — render.yaml, vercel.json, GitHub Actions workflow
  Phase 10: Documentation — README, architecture diagram, agent specs, user guide

--- HARD CONSTRAINTS ---
  - Every agent must be its own file under backend/agents/
  - Agents must NEVER be called directly from main.py — always route through planner
  - DuckDB must read from Parquet via read_parquet(), never from raw CSV
  - All LLM outputs must be structured JSON (parse with re.search + json.loads fallback)
  - Each agent does exactly ONE thing — strict single responsibility principle
  - Frontend contains ZERO business logic — only UI rendering and API calls
  - Use model: claude-sonnet-4-6 for all agent LLM calls

Start with Phase 1. After creating each file, show me a quick verification step
(e.g. run a command or print output) so I can confirm it works before we move on.
```

---

## PROJECT BRIEF: Multi-Agent OLAP Business Intelligence Platform

### Why This Tier?
Tier 1 taught you to use AI tools. Tier 2 taught you to build simple AI applications.
Tier 3 teaches you to **architect** AI systems.

Real enterprise BI platforms are not single scripts — they are modular systems where different
components handle different responsibilities. This is solved through **agents** — specialized
modules that each excel at one task, coordinated by a planner that routes requests appropriately.

---

### What You Will Learn

| Skill | Why It Matters |
|-------|----------------|
| Agent Architecture | The dominant pattern for complex AI applications |
| System Design | Breaking complex problems into modular components |
| Database Design | Star schemas — the foundation of enterprise BI |
| API Development | Building backends that serve AI capabilities |
| Orchestration | Coordinating multiple AI components |
| Full-Stack Development | Connecting frontend, backend, and AI layers |

---

### System Architecture

```
FRONTEND (React + TypeScript + Vite + TailwindCSS + Recharts)
        |
API LAYER (FastAPI)
        |
PLANNER / ORCHESTRATOR  ← the brain
        |
+----------+----------+----------+----------+
|          |          |          |          |
Dimension  Cube Ops   KPI Calc   Report     Optional
Navigator             Calculator Generator  Agents 5-7
|          |          |          |          |
+----------+----------+----------+----------+
        |
DATA ACCESS LAYER (DuckDB + Parquet)
        |
STAR SCHEMA DATABASE
```

---

### The Four Required Agents

**Agent 1 — Dimension Navigator**
- Drill-Down: Year → Quarter → Month → Week
- Roll-Up: Week → Month → Quarter → Year
- Drill-Through: raw transaction detail

**Agent 2 — Cube Operations**
- Slice: filter one dimension
- Dice: filter multiple dimensions
- Pivot: reorganize perspective

**Agent 3 — KPI Calculator**
- Year-over-Year (YoY) growth
- Month-over-Month (MoM) change
- Profit margins
- Top-N rankings

**Agent 4 — Report Generator**
- Structured report JSON (title, columns, totals, highlights)
- 2-3 sentence plain-English summary

---

### Optional Agents (For A+ Grade)

- **Visualization Agent** — selects best Recharts chart type, returns config JSON
- **Anomaly Detection Agent** — Z-score outlier detection (no LLM, pure statistics)
- **Executive Summary Agent** — 3-sentence C-suite narrative

---

### The Planner / Orchestrator

The planner receives every user query, calls the LLM to build a routing plan, executes
agents in sequence passing accumulated data downstream, and returns a unified response.

**Example multi-agent flow:**

User: "Compare Q3 vs Q4 2024 by region, drill into the best performer"

1. Cube Operations Agent — Dice: Q3, Q4, 2024
2. KPI Calculator Agent — Q3 vs Q4 comparison metrics
3. Planner identifies best region from results
4. Dimension Navigator Agent — drill down into best region (country level)
5. Report Generator Agent — format combined results
6. Visualization Agent — recommend chart config
7. Executive Summary Agent — 3-sentence narrative

---

### Grading Criteria

| Grade | Requirements |
|-------|-------------|
| 70–79% | All 4 required agents, basic planner, star schema, simple frontend |
| 80–89% | + 1 optional agent, multi-agent coordination, context management, charts |
| 90–100% | + All 3 optional agents, advanced orchestration, PDF/email, deployment, full docs |

---

### Key Success Factors

1. **Think Like an Architect** — build modular, reusable components, not one big script
2. **Separation is Key** — each agent must be independently testable and replaceable
3. **The Planner Matters** — a smart planner makes the system feel genuinely intelligent
4. **Star Schema is Essential** — design this first; every agent depends on it
5. **Documentation is Graded** — explain every design decision clearly
6. **Test Real Queries** — test edge cases and failures, not just the happy path
7. **Think Enterprise** — this should feel like a professional BI tool, not a school project

---

### Example Queries the System Must Handle

**Single-agent (basic):**
1. "Show me total revenue by region"
2. "What were sales in Q3 2024?"
3. "Create a pivot table with products as rows and months as columns"
4. "Calculate YoY growth for 2024"
5. "Show me the top 5 countries by profit"

**Multi-agent (complex):**
6. "Compare revenue between Q3 and Q4 2024, show me by region, then drill into the best region"
7. "Show me YoY growth by category and highlight categories with >20% growth"
8. "What are our profit margins by product category? Show the top 3 and drill into subcategories"
9. "Give me an executive summary of 2024 performance with anomalies flagged"
10. "Show monthly trends for Europe, then pivot to show by country"
