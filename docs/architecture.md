# OLAP Analytics Platform - Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                      Local Development Setup                     │
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │  React Frontend  │         │  FastAPI Backend │              │
│  │  (Vite)          │◄───────►│  (Uvicorn)       │              │
│  │  Port 5173       │         │  Port 8000       │              │
│  └──────────────────┘         └────────┬─────────┘              │
│                                        │                        │
│                         ┌──────────────┴──────────────┐         │
│                         │                             │         │
│                         v                             v         │
│                  ┌─────────────┐            ┌─────────────────┐ │
│                  │  DuckDB     │            │  7 AI Agents    │ │
│                  │  Database   │            │  (Orchestrated  │ │
│                  │  Local File │            │   by Planner)   │ │
│                  └─────────────┘            └─────────────────┘ │
│                                                                  │
│                         ┌──────────────────────┐                │
│                         │   Hugging Face       │                │
│                         │   (Qwen 2.5 LLM)     │                │
│                         └──────────────────────┘                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Frontend Layer
- **React 18 + TypeScript + Vite**: Single-page application with chat-based UI
- **Tailwind CSS**: Utility-first styling with dark theme
- **Recharts**: Data visualization (Line, Bar, Pie, Composed charts)
- **Lucide React**: Icon library
- **Axios**: HTTP client for API calls

### API Layer
- **FastAPI**: REST API with typed endpoints
- **Uvicorn**: ASGI server (runs on port 8000)
- **Pydantic**: Request/response validation
- **CORS Middleware**: Cross-origin support for frontend

### Intelligence Layer
- **Planner Agent**: Routes user queries through specialist agents
- **7 Specialist Agents**: 
  - KPI Calculator (YoY, MoM, top-N metrics)
  - Dimension Navigator (drill-down/roll-up/drill-through)
  - Cube Operations (slice, dice, pivot)
  - Report Generator (formatted tables)
  - Anomaly Detection (Z-score analysis)
  - Executive Summary (business narratives)
  - Visualization Agent (chart recommendations)
- **Hugging Face (Qwen 2.5)**: LLM for natural language processing and function calling
- **Intent Detector**: Part of the orchestrator for query understanding
- **Context Manager**: Maintains conversation history

### Data Layer
- **DuckDB**: In-process analytical database
- **Star Schema**: 
  - Fact table: fact_sales
  - Dimensions: dim_date, dim_geography, dim_product, dim_customer
- **Local File Storage**: olap.duckdb stored in data/ folder
- **CSV Import**: Sales data generated from sales_data.csv using `load_data.py`

### Processing Pipeline
1. Natural language query from user
2. Intent detection and routing
3. Agent orchestration (Planner selects agents)
4. DuckDB SQL execution
5. Results aggregation
6. Enrichment (anomalies, summaries, charts)
7. Response formatting

## Data Flow

1. User types business question in chat interface
2. React sends POST to `/api/query/` with question and conversation history
3. FastAPI receives request, passes to Intent Detector
4. Planner orchestrates appropriate agents
5. Agents generate and execute DuckDB SQL queries
6. Results enriched with:
   - Anomalies (AnomalyDetectionAgent)
   - Executive summary (ExecutiveSummaryAgent)
   - Chart recommendations (VisualizationAgent)
7. Response returns to frontend with:
   - Data rows
   - Anomalies detected
   - Narrative summary
   - Chart configuration
8. React renders results with chart and table

## API Endpoints

### Natural Language Queries
- `POST /api/query/` - Submit natural language query
- `GET /api/query/dashboard` - Get KPI cards
- `GET /api/query/suggestions` - Example queries

### OLAP Operations
- `POST /api/olap/drill-down` - Hierarchy drill-down
- `POST /api/olap/roll-up` - Aggregate hierarchy
- `POST /api/olap/slice` - Single dimension filter
- `POST /api/olap/dice` - Multiple dimension filter
- `POST /api/olap/pivot` - Cross-tabulation

### KPI Calculations
- `POST /api/olap/kpi/yoy-growth` - Year-over-year
- `POST /api/olap/kpi/mom-change` - Month-over-month
- `POST /api/olap/kpi/margins` - Profit analysis
- `POST /api/olap/kpi/top-n` - Rankings
- `POST /api/olap/kpi/compare` - Period comparison
- `POST /api/olap/kpi/revenue-share` - Share analysis

### Utilities
- `GET /health` - Health check
- `GET /docs` - API documentation
- `GET /schema` - Database schema info

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + Vite | Modern web UI |
| Styling | Tailwind CSS | Responsive design |
| Charts | Recharts | Data visualization |
| Backend | FastAPI + Uvicorn | REST API server |
| Database | DuckDB | Analytical queries |
| LLM | Hugging Face / Qwen 2.5 | NLP and tool calling |
| Validation | Pydantic | Type safety |

## Development Environment

- **Language**: Python 3.11 (backend), JavaScript/TypeScript (frontend)
- **Package Manager**: pip (Python), npm (JavaScript)
- **Dev Server**: Uvicorn (backend), Vite (frontend)
- **Database**: DuckDB (local file: data/olap.duckdb)

## Key Features

✅ **Multi-Agent Architecture**: 8 specialized agents for different operations
✅ **Natural Language Interface**: Chat-based query interface
✅ **OLAP Operations**: Drill, slice, dice, pivot transformations
✅ **Intelligent Enrichment**: Auto-detect anomalies, generate summaries, recommend charts
✅ **Dark Theme UI**: Professional, accessible interface
✅ **Local First**: Works entirely on local machine without cloud dependencies
✅ **Conversation Context**: Maintains history for follow-up queries

## Database Schema

### fact_sales (Main Fact Table)
- sale_id (PK)
- order_id
- date_id (FK)
- geo_id (FK)
- product_id (FK)
- customer_id (FK)
- quantity
- unit_price
- revenue
- cost
- profit
- profit_margin

### Dimensions
- **dim_date**: Date, year, quarter, month
- **dim_geography**: Region, country
- **dim_product**: Category, subcategory
- **dim_customer**: Customer segment

## Running the Application

### Backend
```bash
cd backend
python main.py
# Runs on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### API Documentation
```
http://localhost:8000/docs
```- **CloudFront**: Global edge caching for frontend assets
- **Context Manager**: Currently in-memory; swap to Redis/DynamoDB for multi-instance deployment
- **Agent Pipeline**: Sequential execution; could be parallelized for independent agents
