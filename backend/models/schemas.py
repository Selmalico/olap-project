from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ── Request models ─────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    history: Optional[List[Dict]] = []


class AgentResult(BaseModel):
    agent_name: str
    data: Optional[List[Dict]] = None
    sql: Optional[str] = None
    chart_config: Optional[Dict] = None
    narrative: Optional[str] = None
    anomalies: Optional[List[str]] = None
    kpis: Optional[Dict] = None
    error: Optional[str] = None


class QueryResponse(BaseModel):
    conversation_id: str
    agents_used: List[str]
    results: List[Dict]
    executive_summary: Optional[str] = None
    follow_up_questions: List[str] = []


class ExportRequest(BaseModel):
    conversation_id: str
    results: List[Dict]
    query: str
    title: str = "OLAP Analysis Report"


class EmailRequest(BaseModel):
    to_email: str
    subject: str
    conversation_id: str
    results: List[Dict]
    query: str


# ── Response models (for OpenAPI docs and typing) ─────────────────────────────

class SummaryBlock(BaseModel):
    """Executive summary block returned by NL query and KPI endpoints."""
    text: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class NaturalLanguageQueryResponse(BaseModel):
    """Response shape for POST /api/query/."""
    query: str
    results: List[Dict]
    reports: List[Dict]
    summary: SummaryBlock
    llm_used: bool = False
    conversation_id: Optional[str] = None
    error: Optional[str] = None


class OlapSuccessResponse(BaseModel):
    """Response shape for OLAP operation endpoints (slice, dice, pivot, drill, KPI, etc.)."""
    data: Dict[str, Any] = Field(description="Raw agent result (operation, rows, columns, etc.)")
    report: Dict[str, Any] = Field(description="Formatted table report")
    summary: Optional[SummaryBlock] = Field(None, description="Present for KPI endpoints only")


class ErrorDetail(BaseModel):
    """Structured error body for 4xx/5xx responses."""
    message: str
    error: Optional[str] = None
    traceback: Optional[str] = None
