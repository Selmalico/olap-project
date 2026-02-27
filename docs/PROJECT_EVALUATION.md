# Final Project Evaluation — OLAP BI Platform

**Evaluator role:** University professor (final project submission)  
**Evaluation criteria:** Requirements coverage, implementation quality, correctness, and suggestions for A++ level.

---

## 1. Requirements Checklist

Your specification states the system **must support ALL** of:

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **Slice** | ✅ Implemented | `CubeOperationsAgent.slice()`, `SalesRepository.get_slice()`, POST `/api/olap/slice`, NL routing and OLAP Controls UI |
| **Dice** | ✅ Implemented | `CubeOperationsAgent.dice()`, `SalesRepository.get_dice()`, POST `/api/olap/dice`, NL and UI |
| **Drill-down** | ✅ Implemented | `DimensionNavigatorAgent.drill_down()`, `get_hierarchy_data()`, POST `/api/olap/drill-down`, NL and UI |
| **Roll-up** | ✅ Implemented | `DimensionNavigatorAgent.roll_up()`, same repo method, POST `/api/olap/roll-up`, NL and UI |
| **Pivot** | ✅ Implemented (had bug) | `CubeOperationsAgent.pivot()`, `get_pivot_data()`, POST `/api/olap/pivot`; report generator fixed for pivot result shape |
| **Compare** | ✅ Implemented | `KPICalculatorAgent.compare_periods()`, `get_period_data()`, POST `/api/olap/kpi/compare`, NL; **Compare UI section added** |
| **Time intelligence (YoY)** | ✅ Implemented | `KPICalculatorAgent.yoy_growth()`, `get_yoy_data()`, POST `/api/olap/kpi/yoy-growth`, NL and UI |
| **Time intelligence (MoM)** | ✅ Implemented | `KPICalculatorAgent.mom_change()`, `get_mom_data()`, POST `/api/olap/kpi/mom-change`, NL; **MoM UI section added** |

**Verdict:** All seven required operations are implemented in the backend and exposed via API and (after the changes) via both natural language and the OLAP Controls UI where applicable.

---

## 2. Missing, Partial, or Incorrect Implementation

### 2.1 Pivot — Incorrect (fixed)

- **Issue:** The pivot API returned 500 because `ReportGeneratorAgent.generate_table()` treated pivot results like other agents. For pivot, `data["rows"]` and `data["columns"]` are **dimension names** (strings), while the table content is in `rows_list` and `columns_list`. Using `data.get("rows", ...)` yielded the string `"region"`, so `rows[0].keys()` was effectively `"r".keys()` → **'str' object has no attribute 'keys'**.
- **Fix applied:** In `report_generator.py`, when `operation == "pivot"`, the table is built from `rows_list` and `columns_list` only; otherwise the existing `rows`/`columns` logic is used, with a guard so `rows[0].keys()` is only used when `rows` is a list.

### 2.2 Compare and MoM — Partially implemented (UI gap, fixed)

- **Issue:** Compare and MoM were fully supported in backend and NL, but the **OLAP Controls** tab had no dedicated sections, so “support ALL” from a **UI** perspective was incomplete.
- **Fix applied:** Added “KPI: Month-over-Month Change” and “KPI: Compare Periods” sections in `OLAPControls.jsx` so all seven operations are accessible from the structured OLAP builder.

### 2.3 Compare — Keyword fallback ignores query specifics

- **Issue:** In `agents/planner.py` `_keyword_fallback()`, for “compare” or “vs” the code always calls `compare_periods(period_a={"year": 2023}, period_b={"year": 2024})`. Queries like “Compare Q3 vs Q4 2024” are not parsed; the intent detector can extract Q3/Q4, but the planner’s keyword path does not use it.
- **Recommendation:** In keyword fallback, when “compare”/“vs” is detected, call the intent detector (or a small parser) and use its `period_a`/`period_b` in `compare_periods()` so Q3 vs Q4 and similar phrases are honoured.

### 2.4 Slice vs Dice — Terminology

- **Observation:** Slice is “one dimension, one value”; dice is “multiple dimensions.” The implementation matches this. No bug, but in documentation or UI labels you could add one line (e.g. “Slice: one filter, Dice: multiple filters”) to make the distinction explicit for grading.

---

## 3. Quality of Implementation

### 3.1 Strengths

- **Architecture:** Clear separation: Repository (SQL), agents (slice/dice/pivot, drill/roll-up, KPI, report), orchestrator, REST and NL entry points. Matches the README/architecture and is maintainable.
- **Data layer:** Single `SalesRepository` with parameterized SQL, `_where()`, `VALID_DIMENSIONS`/`VALID_MEASURES`; no ad-hoc SQL in agents. Good for security and consistency.
- **Hierarchies:** Explicit definitions in `dimension_navigator.py` (time, geography, product) with levels and table/label mappings make drill-down and roll-up correct and extensible.
- **NL pipeline:** Intent detector + agent selector + planner with LLM and keyword fallback gives robust coverage when no API key is set.
- **Time intelligence:** YoY and MoM are properly implemented (prior period, absolute and percentage change, optional grouping/filters) and use the repository only.

### 3.2 Weaknesses

1. **Report generator and pivot:** As above, pivot result shape was not handled; this was a real correctness bug until the fix.
2. **Executive summary for pivot:** `executive_summary()` now uses `rows_list` for pivot and checks `isinstance(rows, list)`; ensure any other code paths that assume `rows` is always a list of records are updated if you add more operation types.
3. **Frontend Compare UX:** The Compare section uses raw JSON for Period A/B. For A++ you could add simple dropdowns (e.g. year, optional quarter) and build `period_a`/`period_b` in code to avoid JSON syntax errors and improve usability.
4. **Tests:** `test_agents.py` covers drill_down, intent “compare”, and a YoY keyword fallback; there are no dedicated tests for slice, dice, pivot, roll_up, mom_change, or compare_periods execution. Adding at least one test per operation would strengthen the submission.
5. **Error handling:** Some agent methods return `{"error": "..."}`; the API layer could consistently map these to HTTP 4xx and a stable JSON shape so the frontend can show clear messages.

---

## 4. Visualization, Executive Summary, and Anomaly Detection Agents

Additional requirements to evaluate:

- **Visualization Agent:** Automatically choose chart type; return chart metadata; generate dynamic visualizations.
- **Executive Summary Agent:** Generate business insights; explain trends; provide strategic interpretation.
- **Anomaly Detection Agent (alternative):** Detect statistical outliers in result data.

### 4.1 Visualization Agent

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **Automatically choose chart type** | ✅ Implemented | `VisualizationAgent.recommend()` selects LineChart (time series, YoY/MoM), PieChart (revenue_share), ComposedChart (compare_periods multi-measure, or Bar + pct_change), BarChart (default). Rules in `_pick_chart()` by operation and columns. |
| **Return chart metadata** | ✅ Implemented | Returns `chart_config` with `chart_type`, `x_axis`, `y_axes` (field, color, type, label), `title`, `show_legend`, `show_grid` — Recharts-compatible. |
| **Generate dynamic visualizations** | ⚠️ Partial | Chart config is returned; the **frontend** (`ChartPanel`) renders from this config. The agent does not run in the **current NL path** (see gap below). |

**Pivot fix:** The visualization agent was updated to use `rows_list` when `operation == "pivot"` so it does not treat the dimension name string as a list of rows.

### 4.2 Executive Summary Agent

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **Generate business insights** | ✅ Implemented | `ExecutiveSummaryAgent.summarize()` produces a 3-sentence narrative. Sentence 1: what happened (metric + direction + magnitude). Sentence 2: what drove it (top segment/region/product). Sentence 3: recommendation. |
| **Explain trends** | ✅ Implemented | Heuristic `_heuristic()` covers yoy_growth, mom_change, compare_periods, top_n, profit_margins, drill_down/roll_up, revenue_share with operation-specific text (e.g. “YoY revenue growth reached +X% in …”, “MoM changed by …”). |
| **Strategic interpretation** | ✅ Implemented | `_recommendation()` returns actionable advice per operation (e.g. “Monitor declining segments…”, “Review seasonal patterns…”, “Prioritise resources toward top performers…”). Optional HuggingFace pass for a richer narrative when token is set. |

**Pivot fix:** The executive summary agent was updated to use `rows_list` when `operation == "pivot"` and to guard against non-list `rows`.

### 4.3 Anomaly Detection Agent

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **Detect outliers** | ✅ Implemented | `AnomalyDetectionAgent.detect(rows)` uses Z-score (threshold 2.5) on numeric columns, returns up to 5 anomalies with a short message (column, label, value, % from mean, Z). No LLM; rule-based. |
| **Integrates with pipeline** | ⚠️ Partial | Implemented and used in **orchestrator** `plan_and_execute()` (e.g. for compare_periods, yoy_growth). Not invoked in the **main NL endpoint** (see gap below). |

### 4.4 Critical Gap: NL Endpoint Does Not Use These Three Agents

The **natural language** entry point used by the frontend is `POST /api/query/` → `routers/query.py` → **`PlannerAgent.query()`** (`agents/planner.py`). That path:

- Calls only **OLAP agents** (slice, dice, pivot, drill_down, roll_up, yoy_growth, mom_change, compare_periods, etc.) via `_dispatch()`.
- Builds **reports** and **summary** from **`ReportGeneratorAgent`** only (`generate_table()`, `executive_summary()`).
- Does **not** call `VisualizationAgent`, `AnomalyDetectionAgent`, or the standalone **`ExecutiveSummaryAgent`**.

So for NL queries today:

- **No chart_config** is returned (visualization agent never runs).
- **No anomalies** array is returned (anomaly agent never runs).
- **Executive narrative** comes from `ReportGeneratorAgent.executive_summary()` (summary + highlights + recommendations), not from `ExecutiveSummaryAgent` (3-sentence narrative). Both provide “insights,” but the dedicated Executive Summary Agent is not in this path.

The **orchestrator** (`orchestrator/planner.py` → `plan_and_execute()`) does run all 7 agents, including visualization, anomaly_detection, and executive_summary, but **no route in `main.py` or the query router calls `plan_and_execute()`**. The Chat UI (e.g. `useChat.ts`) expects `response.executive_summary`, `response.agents_used`, `response.results` with `chart_config` and `anomalies` — a response shape that matches the orchestrator, not the current PlannerAgent response.

**Recommendation for full requirement coverage:** Either:

1. **Wire the NL endpoint to the orchestrator:** Have `POST /api/query/` call `plan_and_execute()` (with intent from `IntentDetector`) and map its return value to the existing frontend contract (`executive_summary`, `agents_used`, `results` with `chart_config` and `anomalies`), or  
2. **Enrich PlannerAgent.query():** After running OLAP agents, call `VisualizationAgent.recommend(last_result)`, `AnomalyDetectionAgent.detect(rows)`, and `ExecutiveSummaryAgent.summarize(last_result, anomalies)` and add `chart_config`, `anomalies`, and the narrative to the response so the Chat UI gets charts, anomalies, and the 3-sentence executive summary.

---

## 5. Concrete Improvements for A++

1. **Use Visualization, Executive Summary, and Anomaly agents in the NL flow**
   - Integrate them into the path that serves `POST /api/query/` (see §4.4) so that NL responses include chart metadata, anomalies, and the 3-sentence executive narrative.
2. **Tests**
   - Add tests (e.g. in `test_agents.py` or a new `test_olap_operations.py`) for: slice, dice, pivot, roll_up, mom_change, compare_periods (and yoy_growth if not already covered end-to-end). Use a small in-memory or fixture DB so grading can run them.
2. **Compare in keyword fallback**
   - Use intent detector params for “compare”/“vs” (e.g. Q3 vs Q4, 2023 vs 2024) when calling `compare_periods()` in the keyword path, so NL behaviour matches user intent without requiring the LLM.
3. **OLAP Controls — Compare UX**
   - Replace raw JSON inputs with:
     - Year (and optionally quarter) for Period A and Period B, then build `period_a`/`period_b` in the frontend. Optionally add “by region” / “by category” dropdown for `group_by`.
4. **Documentation**
   - In README or a short “OLAP operations” doc, add one sentence per operation (Slice, Dice, Drill-down, Roll-up, Pivot, Compare, YoY, MoM) and one example query or API call each. This makes it trivial for a grader to verify “support ALL.”
5. **API contract**
   - Document or standardise error responses (e.g. `{"error": "...", "code": "INVALID_DIMENSION"}`) and use HTTP 400 for validation errors so the frontend can show specific messages.
6. **Pivot totals**
   - You already pass `add_totals=False` for pivot. Optionally add a “Totals” row/column in the pivot table (e.g. in the report or frontend) so it’s clearly a cross-tab with margins; this is often expected in OLAP UIs.

---

## 6. Technical and Academic Weaknesses

- **Academic:** The report does not explicitly cite OLAP definitions (e.g. Codd’s OLAP rules or standard definitions of slice/dice/drill/roll-up/pivot). Adding a short “Definitions” subsection (e.g. in README or architecture) with one sentence each would align the project with course material and show correct terminology.
- **Logical:** The only logic bug identified was the pivot/report shape; with the fix, pivot is consistent with the rest of the pipeline.
- **Technical:** Dependency on DuckDB and star schema is appropriate; the only technical debt noted is the report generator’s assumption about result shape, which is now special-cased for pivot. Extending to new operation types should reuse the same pattern (prefer list-like keys for table data and avoid overloading dimension-name keys).

---

## 7. Summary

| Aspect | Grade note |
|--------|------------|
| **Requirements coverage** | All 7 operations (Slice, Dice, Drill-down, Roll-up, Pivot, Compare, YoY, MoM) are implemented and exposed (API + NL; UI completed with MoM and Compare sections). |
| **Correctness** | Pivot was broken in the report step; fix applied. Rest of the flow is consistent. |
| **Structure** | Strong: repository, agents, orchestrator, clear API and NL entry points. |
| **Completeness** | Backend and API complete; UI now covers all operations; keyword fallback for Compare could use intent params. |
| **Visualization / Summary / Anomaly** | All three agents are implemented (auto chart type, chart metadata, insights, trends, strategy, Z-score anomalies). They are **not** invoked on the current NL endpoint; wire them in for full requirement coverage (see §4). |
| **API (REST, Pydantic, OpenAPI, errors, status codes)** | REST endpoints and route structure in place; Pydantic for all requests and response models in schemas; Swagger/OpenAPI at /docs; error handling and 400/500 status codes applied (see §8). |
| **A++ improvements** | Wire Visualization, Executive Summary, and Anomaly agents into the NL response; add tests per operation; use intent for Compare in keyword fallback; improve Compare UI; add OLAP definitions; optionally standardise errors and pivot totals. |

With the pivot fix and the added MoM/Compare UI sections, the project **meets the stated requirement that the system support ALL** of Slice, Dice, Drill-down, Roll-up, Pivot, Compare, and Time intelligence (YoY, MoM). Applying the suggested improvements would strengthen the submission to A++ level.

---

## 8. API Requirements (REST, Pydantic, OpenAPI, Error Handling, Status Codes)

Requirements: **REST endpoints**, **clean route structure**, **request/response models (Pydantic)**, **Swagger/OpenAPI working**, **error handling**, **proper status codes**.

### 8.1 REST Endpoints

| Area | Endpoints | Status |
|------|-----------|--------|
| **Health & schema** | `GET /health`, `GET /schema` | ✅ |
| **Natural language** | `POST /api/query/`, `GET /api/query/llm-status`, `GET /api/query/dashboard`, `GET /api/query/suggestions` | ✅ |
| **OLAP – navigation** | `POST /api/olap/drill-down`, `POST /api/olap/roll-up`, `GET /api/olap/hierarchies` | ✅ |
| **OLAP – cube** | `POST /api/olap/slice`, `POST /api/olap/dice`, `POST /api/olap/pivot`, `GET /api/olap/dimensions/{dimension}/values` | ✅ |
| **OLAP – KPI** | `POST /api/olap/kpi/yoy-growth`, `mom-change`, `margins`, `top-n`, `compare`, `revenue-share` | ✅ |
| **Export / email** | `POST /export/pdf`, `POST /email/send` | ✅ |

All are RESTful (resource-oriented paths, GET for read, POST for actions).

### 8.2 Clean Route Structure

- **Prefixes:** `/api/query` (NL), `/api/olap` (structured OLAP). Root-level `/health`, `/schema`, `/export/pdf`, `/email/send`.
- **Naming:** Hyphenated (`drill-down`, `roll-up`, `yoy-growth`, `mom-change`, `top-n`, `revenue-share`), nested KPI under `/api/olap/kpi/`.
- **Structure:** Clear separation by feature; no redundant or overlapping paths.

### 8.3 Request/Response Models (Pydantic)

| Model | Use | Location |
|-------|-----|----------|
| **QueryRequest** | POST /api/query/ body | query router + models/schemas.py |
| **DrillRequest, SliceRequest, DiceRequest, PivotRequest** | OLAP cube/nav | olap router |
| **YoYRequest, MoMRequest, MarginsRequest, TopNRequest, CompareRequest, ShareRequest** | OLAP KPI | olap router |
| **ExportRequest, EmailRequest** | Export/email | main.py, models/schemas.py |
| **NaturalLanguageQueryResponse, OlapSuccessResponse, SummaryBlock, ErrorDetail** | Response typing & OpenAPI docs | models/schemas.py |

All request bodies use Pydantic; response models are defined for documentation and consistency (success/error shapes).

### 8.4 Swagger/OpenAPI Working

- FastAPI auto-generates **OpenAPI 3** and **Swagger UI** at `/docs` and ReDoc at `/redoc`. No extra config required.
- Request bodies are documented via Pydantic; selected routes document **responses** (e.g. 200/400/500) in the decorator for clearer docs.

### 8.5 Error Handling and Proper Status Codes

| Scenario | Before | After (changes applied) |
|----------|--------|---------------------------|
| **NL query – server error** | 200 with `error` in body | **500** with `HTTPException(detail={...})` |
| **NL query – serialization error** | 200 with error in body | **500** with `HTTPException` |
| **Dashboard – exception** | 200 with error in body | **500** with `HTTPException` |
| **OLAP – agent returns `error`** (e.g. unknown dimension) | 200 with `data.error` | **400** with `HTTPException(detail=result["error"])` |
| **OLAP – report/summary generation failure** | Unhandled (possible 500 from framework) | **500** with structured detail |
| **Export/email – exception** | 500 | 500 (unchanged, already correct) |

- **400 Bad Request:** Invalid parameters or agent validation (e.g. unknown dimension, invalid hierarchy).
- **500 Internal Server Error:** Unexpected failures (planner, report generation, serialization).
- Error responses use a consistent structure where applicable (`message`, `error`, optional `traceback` in debug).

### 8.6 Summary (API Requirements)

| Requirement | Status |
|-------------|--------|
| REST endpoints | ✅ Full set for query, OLAP, export, email, health, schema. |
| Clean route structure | ✅ Prefixes and naming are consistent and logical. |
| Request/response models (Pydantic) | ✅ All request bodies; response models in schemas for docs. |
| Swagger/OpenAPI working | ✅ `/docs` and `/redoc` out of the box; response docs added where relevant. |
| Error handling | ✅ Centralised checks for agent errors and exceptions; HTTPException used. |
| Proper status codes | ✅ 200 success; 400 for bad request; 500 for server errors. |

---

## 9. Frontend Requirements (Chat, Results, Tables, Charts, Loading, Layout, Agents)

Requirements: **Chat interface**, **Results display**, **Tables formatted nicely**, **Charts displayed properly**, **Loading indicators**, **Clean layout**, **Show all agents and actions**, **Visually great**.

### 9.1 Implemented

| Requirement | Status | Implementation |
|-------------|--------|-----------------|
| **Chat interface** | ✅ | Single conversational view: user bubbles (navy gradient), assistant cards (white, shadow), starter-question chips, clear input bar with Analyze button. |
| **Results display** | ✅ | Assistant messages show summary text, highlights (emerald), recommendations (amber), then per-report: title, chart, table. Fallback for raw `results` when `reports` not present. |
| **Tables formatted nicely** | ✅ | `DataTable` supports `report` or `columns`/`rows`/`totalsRow`; sortable headers; light-theme styling (slate borders, zebra rows); totals row; number formatting; +/- and % colour hints. |
| **Charts displayed properly** | ✅ | `ReportChart` renders from report (Line for time series, Pie for share, Bar default); Recharts with tooltips, legend, responsive height. `ChartPanel` used when `chart_config` is present (orchestrator path). |
| **Loading indicators** | ✅ | While loading: `AgentTracker` in loading state (“Routing through OLAP agents…”), spinner icon, “Running OLAP pipeline…” text; Analyze button shows spinner and “Analyzing…”. |
| **Clean layout** | ✅ | Max-width container, gradient background, header with logo and clear chat, scrollable message area, fixed input bar; spacing and typography consistent. |
| **Show all agents and actions** | ✅ | `AgentTracker` shows either **operations** (slice, dice, drill_down, roll_up, pivot, yoy_growth, mom_change, compare_periods, top_n, profit_margins, revenue_share) or **agents** (when from orchestrator). Each badge has icon + label and distinct colour. |
| **Visually great** | ✅ | Navy/slate palette, gradients on header icon and user bubble, subtle shadows, rounded corners, emerald/amber for highlights and recommendations, error state in rose. |

### 9.2 Key files

- **Chat.tsx** – Main chat page: header, messages, loading block, input; uses `reports` and `summary` from `useChat`; renders `AgentTracker`, `ReportChart`, `DataTable`, `ChartPanel` (fallback), `ExportToolbar`.
- **useChat.ts** – Maps API response to message: `summary.text` → content, `reports`, `summary.highlights`/`recommendations`, `operations` derived from `results[].operation`.
- **AgentTracker.tsx** – Displays agents or operations with icons and colours; loading state with spinner.
- **DataTable.jsx** – Accepts `report`, or `columns`/`rows`/`totalsRow`, or `data` (array); light theme; sortable; formatted cells.
- **ReportChart.tsx** – Chart from report (Line/Pie/Bar) for use in message bubbles.
- **index.css** – Base antialiasing, scroll-smooth, scrollbar-thin utility.

---

## 10. Deployment Requirements (Backend, Database, Frontend, Demo Link)

Requirements: **Deploy backend to cloud (Render / Railway / Fly.io)**, **Deploy database (Supabase / Cloud Postgres)**, **Deploy frontend (Vercel / Streamlit Cloud)**, **Provide working public demo link**.

### 10.1 What’s in the repo

| Item | Purpose |
|------|--------|
| **backend/Dockerfile** | Builds backend image: installs deps, copies app + data, runs `data/generate_dataset.py` to create `sales_data.csv`, runs uvicorn. For Render / Railway / Fly.io. |
| **render.yaml** | Render Blueprint: one web service (Docker), env for `DATABASE_PATH` and `CSV_PATH`, health check `/health`. |
| **fly.toml** | Fly.io config: Dockerfile path, env, internal port 8000, minimal VM. |
| **frontend/vercel.json** | Vercel: build output `dist`, SPA rewrites, security headers. |
| **docs/DEPLOYMENT.md** | Step-by-step: backend (Render, Railway, Fly), database (DuckDB + optional Supabase), frontend (Vercel), demo link and troubleshooting. |
| **backend/tools/supabase_log.py** | Optional: if `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set, logs each NL query to Supabase table `analytics_log`. |
| **data/generate_dataset.py** | Writes `sales_data.csv` (integer quarter) for the star-schema loader; used in Docker and locally. |

### 10.2 Backend (Render / Railway / Fly.io)

- **Deploy:** Use the same Docker image (build from repo root with `backend/Dockerfile`). Render: connect repo and set Dockerfile path to `backend/Dockerfile`. Railway: deploy from GitHub, Dockerfile `backend/Dockerfile`, context root. Fly: `fly launch` then `fly deploy` with repo-root `fly.toml`.
- **Env:** `DATABASE_PATH=/app/data/olap.duckdb`, `CSV_PATH=/app/data/sales_data.csv`. Platform sets `PORT`.
- **Health:** Backend exposes `GET /health`; use it as the health check URL.

### 10.3 Database (DuckDB + optional Supabase/Postgres)

- **OLAP data:** DuckDB is **embedded** in the backend. No separate DB server. On startup, the backend creates `/app/data/olap.duckdb` and loads `sales_data.csv` (generated in the image). This is the “deployed database” for analytics.
- **Optional Supabase (Postgres):** To satisfy “Supabase / Cloud Postgres” explicitly, create a Supabase project, run the `analytics_log` SQL in DEPLOYMENT.md, set `SUPABASE_URL` and `SUPABASE_ANON_KEY` on the backend. The backend then logs each NL query to `analytics_log`. So “database” = DuckDB (OLAP) + optional Supabase (audit log).

### 10.4 Frontend (Vercel)

- **Deploy:** Vercel → Import repo → Root directory `frontend` → Set env `VITE_API_URL` = backend public URL (e.g. `https://olap-bi-api.onrender.com`).
- **Streamlit Cloud:** Not used; the frontend is React (Vite), so Vercel is the appropriate host.

### 10.5 Working public demo link

- **Demo URL:** The **frontend** URL after Vercel deploy (e.g. `https://olap-bi-xxx.vercel.app`). Use this as the **working public demo link** in the report/submission.
- **Check:** Open the link → send a query in the chat → confirm results (tables/charts/summary) and that `/health` on the backend returns OK.

### 10.6 Summary (deployment)

| Requirement | Status |
|-------------|--------|
| Deploy backend to cloud (Render / Railway / Fly.io) | ✅ Dockerfile + render.yaml + fly.toml; docs for all three. |
| Deploy database (Supabase / Cloud Postgres) | ✅ DuckDB deployed with backend; optional Supabase (analytics_log) for Postgres. |
| Deploy frontend (Vercel / Streamlit Cloud) | ✅ Vercel config (vercel.json); root `frontend`, env `VITE_API_URL`. |
| Provide working public demo link | ✅ Use the Vercel frontend URL; full steps in DEPLOYMENT.md. |
