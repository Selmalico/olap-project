# OLAP BI Platform - Architecture

## System Overview

```
+------------------+       +-------------------+       +------------------+
|                  |       |                   |       |                  |
|  React Frontend  +------>+  API Gateway      +------>+  AWS Lambda      |
|  (CloudFront)    |       |  (HTTP API)       |       |  (FastAPI)       |
|                  |       |                   |       |                  |
+------------------+       +-------------------+       +--------+---------+
                                                                |
                                                    +-----------+-----------+
                                                    |                       |
                                                    v                       v
                                            +-------+-------+      +-------+-------+
                                            |   Planner /   |      |   DuckDB      |
                                            |  Orchestrator |      |   Executor    |
                                            +-------+-------+      +-------+-------+
                                                    |                       |
                                    +---------------+---------------+       |
                                    |       |       |       |       |       |
                                    v       v       v       v       v       v
                                +-----+ +-----+ +-----+ +-----+ +-----+ +--------+
                                |Dim  | |Cube | |KPI  | |Viz  | |Exec | |S3      |
                                |Nav  | |Ops  | |Calc | |Agent| |Summ | |Parquet |
                                +-----+ +-----+ +-----+ +-----+ +-----+ +--------+
                                    |       |       |
                                    v       v       v
                                +-----+ +-----+ +-----+
                                |Rpt  | |Anom | |PDF  |
                                |Gen  | |Det  | |Gen  |
                                +-----+ +-----+ +--+--+
                                                    |
                                            +-------+-------+
                                            |       |       |
                                            v       v       v
                                        +-----+ +-----+ +-----+
                                        | S3  | | SES | | PDF |
                                        |Rpts | |Email| |D/L  |
                                        +-----+ +-----+ +-----+
```

## Component Descriptions

### Frontend Layer
- **React + TypeScript + Vite**: Single-page application with chat-based UI
- **TailwindCSS**: Utility-first styling with custom navy/accent theme
- **Recharts**: Data visualization (Line, Bar, Pie, Composed charts)
- **CloudFront**: CDN distribution for static assets from S3

### API Layer
- **API Gateway**: HTTP API routing requests to Lambda
- **AWS Lambda**: Serverless compute running FastAPI via Mangum adapter
- **FastAPI**: REST API with 5 endpoints (/health, /schema, /query, /export/pdf, /email/send)

### Intelligence Layer
- **Planner/Orchestrator**: Routes user queries to appropriate agents using Claude
- **7 AI Agents**: Specialized Claude-powered agents for different OLAP operations
- **Context Manager**: Maintains conversation history (in-memory, last 20 turns)

### Data Layer
- **DuckDB**: In-process analytical database reading Parquet directly from S3
- **S3 Data Bucket**: Stores Parquet files (fact_sales.parquet)
- **S3 Reports Bucket**: Stores generated PDF reports
- **Star Schema**: Fact table with 4 dimension tables (date, geography, product, customer)

### Export Layer
- **WeasyPrint**: HTML-to-PDF conversion using Jinja2 templates
- **AWS SES**: Email delivery with PDF attachments
- **S3 Presigned URLs**: Temporary download links for PDF reports

## Data Flow

1. User types a business question in the chat UI
2. React sends POST to `/query` with the question and conversation history
3. FastAPI receives request, passes to Planner/Orchestrator
4. Planner calls Claude to determine which agents to invoke
5. Agents execute in sequence, each receiving accumulated data from prior agents
6. SQL-generating agents produce DuckDB queries that read Parquet from S3
7. Results flow through Report Generator, Visualization Agent, and Executive Summary
8. Response returns to frontend with data, chart config, anomalies, and narrative
9. React renders table, chart, agent tracker badges, and follow-up suggestions

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | DuckDB | Zero-config OLAP engine, reads Parquet directly from S3 |
| AI Model | Claude | Strong JSON output, instruction following for SQL generation |
| Backend | FastAPI | Async support, auto-generated OpenAPI docs, Pydantic validation |
| Frontend | React+Vite | Fast dev experience, TypeScript safety, rich ecosystem |
| Deployment | Lambda | Serverless, auto-scaling, pay-per-request |
| PDF | WeasyPrint | CSS-styled HTML to PDF, no external service needed |
| Charts | Recharts | React-native, composable, good defaults |

## Scalability Notes

- **DuckDB + S3**: Scales to billions of rows; Parquet columnar format enables fast aggregations
- **Lambda**: Auto-scales to 1000 concurrent executions by default
- **CloudFront**: Global edge caching for frontend assets
- **Context Manager**: Currently in-memory; swap to Redis/DynamoDB for multi-instance deployment
- **Agent Pipeline**: Sequential execution; could be parallelized for independent agents
