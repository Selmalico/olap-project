# OLAP Analytics Platform

A Multi-Agent OLAP Business Intelligence Platform with natural language queries, advanced analytics, and interactive data exploration.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Access
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Project Structure

```
olap-project/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── config.py
│   ├── utils.py
│   ├── requirements.txt
│   ├── agents/                    # 8 AI agents
│   │   ├── planner.py
│   │   ├── kpi_calculator.py
│   │   ├── dimension_navigator.py
│   │   ├── cube_operations.py
│   │   ├── report_generator.py
│   │   ├── anomaly_detection.py
│   │   ├── executive_summary.py
│   │   └── visualization_agent.py
│   ├── routers/                   # API endpoints
│   │   ├── query.py
│   │   └── olap.py
│   ├── database/                  # DuckDB setup
│   │   ├── connection.py
│   │   └── repository.py
│   ├── models/                    # Data schemas
│   │   └── schemas.py
│   ├── orchestrator/              # Agent orchestration
│   │   ├── agent_selector.py
│   │   ├── context_manager.py
│   │   ├── intent_detector.py
│   │   └── planner.py
│   ├── tools/                     # Utilities
│   │   ├── duckdb_executor.py
│   │   ├── email_sender.py
│   │   ├── pdf_generator.py
│   │   ├── s3_client.py
│   │   └── supabase_log.py
│   └── templates/
│       └── report.html
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main app
│   │   ├── main.jsx
│   │   ├── index.css              # Tailwind styling
│   │   ├── components/            # React components
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── OLAPControls.jsx
│   │   │   ├── ResultsPanel.jsx
│   │   │   ├── DataTable.jsx
│   │   │   └── KPICard.jsx
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── services/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── data/
│   ├── sales_data.csv             # Sample retail data
│   ├── olap.duckdb                # DuckDB database file
│   ├── load_to_parquet.py
│   └── generate_dataset.py        # Generate sample data
│
├── database/
│   ├── load_data.py
│   ├── schema.sql                 # Star schema definition
│   └── migrations/
│
├── docs/
│   ├── architecture.md            # System architecture
│   ├── er_diagram.md              # Entity-Relationship diagram
│   ├── er_diagram.png
│   ├── DEPLOYMENT.md
│   ├── PROJECT_EVALUATION.md
│   └── agents/                    # Agent documentation
│
├── infrastructure/                # Cloud files (reference only)
│   ├── lambda/
│   │   └── handler.py
│   └── cloudformation/
│
├── generate_dataset.py            # Generate sample data
├── README.md
└── .gitignore
```

## Features

### 8 AI Agents

1. **Planner** - Routes natural language queries through specialist agents
2. **KPI Calculator** - Calculates Year-over-Year, Month-over-Month, and top-N metrics
3. **Dimension Navigator** - Drill-down and roll-up operations through hierarchies
4. **Cube Operations** - Slice, dice, and pivot data cube operations
5. **Report Generator** - Generates formatted table reports
6. **Anomaly Detection** - Detects statistical outliers using Z-score analysis
7. **Executive Summary** - Generates business narrative summaries
8. **Visualization Agent** - Recommends optimal chart types for data

### API Endpoints

**Natural Language Queries:**
- `POST /api/query/` - Submit natural language questions
- `GET /api/query/dashboard` - Get KPI cards
- `GET /api/query/suggestions` - Get example queries

**OLAP Operations:**
- `POST /api/olap/drill-down` - Drill down through hierarchies
- `POST /api/olap/roll-up` - Roll up aggregations
- `POST /api/olap/slice` - Slice data on a dimension
- `POST /api/olap/dice` - Filter multiple dimensions
- `POST /api/olap/pivot` - Create pivot tables
- `GET /api/olap/hierarchies` - Get available hierarchies
- `GET /api/olap/dimensions/{dimension}/values` - Get dimension values

**KPI Calculations:**
- `POST /api/olap/kpi/yoy-growth` - Year-over-year growth
- `POST /api/olap/kpi/mom-change` - Month-over-month change
- `POST /api/olap/kpi/margins` - Profit margin analysis
- `POST /api/olap/kpi/top-n` - Top N items by measure
- `POST /api/olap/kpi/compare` - Compare periods
- `POST /api/olap/kpi/revenue-share` - Calculate revenue share

### Database

**Star Schema:**
- **fact_sales** - Central fact table with sales transactions
- **dim_date** - Date dimension (year, quarter, month)
- **dim_geography** - Geography dimension (region, country)
- **dim_product** - Product dimension (category, subcategory)
- **dim_customer** - Customer dimension (customer_segment)

**Data:**
- 10,000+ retail sales records
- Date range: 2022-2024
- Sample data automatically generated on first run

### Frontend Features

- **Chat Interface** - Natural language query input
- **OLAP Controls** - Interactive drill-down, slice, dice, pivot controls
- **Results Panel** - Display query results with auto-generated charts
- **Data Tables** - Sortable, paginated result tables
- **KPI Cards** - Visual metric displays
- **Dark Theme** - Professional dark UI with Tailwind CSS

## Technologies

**Backend:**
- Python 3.11
- FastAPI (Python web framework)
- DuckDB (Analytical database)
- Anthropic Claude (LLM for natural language processing)
- Pydantic (Data validation)
- Uvicorn (ASGI server)

**Frontend:**
- React 18
- Vite (Build tool)
- Tailwind CSS (Styling)
- Recharts (Data visualization)
- Lucide React (Icons)
- Axios (HTTP client)

**Infrastructure:**
- AWS Lambda (reference handler included)
- CloudFormation (templates for reference)

## Development

### Requirements
- Python 3.11+
- Node.js 18+
- pip, npm

### Install Dependencies

Backend:
```bash
cd backend
pip install -r requirements.txt
```

Frontend:
```bash
cd frontend
npm install
```

### Generate Sample Data
```bash
python generate_dataset.py
```

This creates `data/sales_data.csv` with 10,000+ sample retail records.

### Run Locally

Terminal 1 - Backend:
```bash
cd backend
python main.py
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

## API Documentation

Once running, access interactive API docs at:
```
http://localhost:8000/docs
```

## License

MIT License - 2026

